package com.mslab.recommend;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 推荐 BFF（Java）：按 X-Canary 选择 Python 模型服务（recommend / recommend-canary）。
 * 跨语言契约：连接 300ms、读取默认 1s；下游超时或不可用时返回非 null 的降级体（热门商品兜底），
 * 避免「返回 null 导致空指针贯穿业务」（讲义 §5.2.2）。
 */
@SpringBootApplication
@RestController
public class RecommendBffApplication {
  private final RestTemplate http;

  @Value("${mslab.recommend-url:http://recommend:8080}")
  private String recommendUrl;

  @Value("${mslab.recommend-canary-url:http://recommend-canary:8080}")
  private String recommendCanaryUrl;

  /** 可选：按 ai-governor 的延迟预测选路（§10.1）。默认关闭，金丝雀仍由网关哈希决定。 */
  @Value("${mslab.smart-routing:false}")
  private boolean smartRouting;

  @Value("${mslab.router-url:http://ai-governor:8080}")
  private String routerUrl;

  private final RestTemplate routerHttp;
  private volatile String cachedBest;
  private volatile long cachedAtMs;

  public RecommendBffApplication(
      RestTemplateBuilder builder,
      @Value("${mslab.read-timeout-ms:1000}") long readTimeoutMs) {
    this.http = builder
        .setConnectTimeout(Duration.ofMillis(300))
        .setReadTimeout(Duration.ofMillis(readTimeoutMs))
        .build();
    this.routerHttp = builder
        .setConnectTimeout(Duration.ofMillis(300))
        .setReadTimeout(Duration.ofMillis(500))
        .build();
  }

  /** 返回 true 表示走 canary 实例。智能路由失败时回退到网关给出的 X-Canary。 */
  private boolean useCanaryInstance(boolean headerCanary) {
    if (!smartRouting) return headerCanary;
    long now = System.currentTimeMillis();
    if (cachedBest == null || now - cachedAtMs > 5000) {
      try {
        Map<?, ?> r = routerHttp.getForObject(routerUrl + "/route", Map.class);
        Object best = r == null ? null : r.get("best");
        if (best != null) {
          cachedBest = String.valueOf(best);
          cachedAtMs = now;
        }
      } catch (RestClientException e) {
        cachedBest = null;
        return headerCanary;
      }
    }
    return cachedBest == null ? headerCanary : "recommend-canary".equals(cachedBest);
  }

  public static void main(String[] args) {
    SpringApplication.run(RecommendBffApplication.class, args);
  }

  @GetMapping("/health")
  public Map<String, Object> health() {
    return Map.of("ok", true, "service", "recommend-bff");
  }

  @GetMapping("/api/recommend")
  public ResponseEntity<Object> recommend(
      @RequestHeader(value = "X-User-Id", required = false) String userId,
      @RequestHeader(value = "X-Canary", required = false) String canary,
      @RequestHeader(value = "X-Experiment", required = false) String experiment) {
    boolean isCanary = useCanaryInstance("true".equalsIgnoreCase(canary));
    String exp = experiment == null ? "ranker_v1" : experiment;
    String baseUrl = isCanary ? recommendCanaryUrl : recommendUrl;
    HttpHeaders headers = new HttpHeaders();
    headers.set("X-User-Id", userId == null ? "anonymous" : userId);
    headers.set("X-Canary", canary == null ? "false" : canary);
    headers.set("X-Experiment", exp);
    try {
      ResponseEntity<String> resp = http.exchange(baseUrl + "/api/recommend", HttpMethod.GET,
          new HttpEntity<>(headers), String.class);
      return ResponseEntity.ok()
          .header("X-Canary", canary == null ? "false" : canary)
          .header("X-Experiment", exp)
          .header("X-Version", isCanary ? "v2" : "v1")
          .header("Content-Type", "application/json")
          .body(resp.getBody());
    } catch (RestClientException e) {
      return ResponseEntity.ok()
          .header("X-Canary", canary == null ? "false" : canary)
          .header("X-Experiment", exp)
          .header("X-Version", "fallback")
          .header("X-Degraded", "true")
          .header("Content-Type", "application/json")
          .body(fallbackBody(userId, exp, isCanary, e));
    }
  }

  /** 非 null 降级体：热门商品前 8 个，score 为 0，明确标注 degraded。 */
  private Map<String, Object> fallbackBody(String userId, String exp, boolean canary, Exception cause) {
    List<Map<String, Object>> items = new ArrayList<>();
    for (int i = 1; i <= 8; i++) {
      items.add(Map.of("sku", "sku-" + i, "score", 0.0));
    }
    Map<String, Object> body = new HashMap<>();
    body.put("user_id", userId == null ? "anonymous" : userId);
    body.put("experiment", exp);
    body.put("model_version", "fallback");
    body.put("canary", canary);
    body.put("degraded", true);
    body.put("message", cause.getClass().getSimpleName() + ": " + cause.getMessage());
    body.put("items", items);
    return body;
  }
}
