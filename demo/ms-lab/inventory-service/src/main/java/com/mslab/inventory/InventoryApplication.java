package com.mslab.inventory;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
@RestController
public class InventoryApplication {
  private final ConcurrentHashMap<String, AtomicInteger> stock = new ConcurrentHashMap<>();
  private final AtomicInteger chaosMs = new AtomicInteger(0);

  @Autowired(required = false)
  private StringRedisTemplate redis;

  public InventoryApplication() {
    for (int i = 1; i <= 20; i++) {
      stock.put("sku-" + i, new AtomicInteger(i == 1 ? 500 : 100));
    }
  }

  public static void main(String[] args) {
    SpringApplication.run(InventoryApplication.class, args);
  }

  @GetMapping("/health")
  public Map<String, Object> health() {
    return Map.of("ok", true, "service", "inventory-service", "chaosLatencyMs", chaosMs.get());
  }

  @PostMapping("/chaos/latency")
  public Map<String, Object> chaos(@RequestBody Map<String, Object> body) {
    int ms = ((Number) body.getOrDefault("ms", 0)).intValue();
    chaosMs.set(ms);
    return Map.of("chaosLatencyMs", ms);
  }

  @GetMapping("/api/inventory/{sku}")
  public Map<String, Object> get(@PathVariable("sku") String sku) {
    AtomicInteger q = stock.get(sku);
    if (q == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "sku not found");
    return Map.of("sku", sku, "qty", q.get());
  }

  @PostMapping("/api/inventory/{sku}/reserve")
  public Map<String, Object> reserve(@PathVariable("sku") String sku,
                                    @RequestBody Map<String, Object> body,
                                    @RequestHeader(value = "X-Idempotency-Key", required = false) String idem) {
    sleepChaos();
    String orderId = String.valueOf(body.getOrDefault("orderId", body.get("order_id")));
    int qty = ((Number) body.getOrDefault("qty", 1)).intValue();
    String key = idem != null ? idem : ("reserve-" + orderId + ":" + sku);
    if (redis != null) {
      Boolean ok = redis.opsForValue().setIfAbsent("idem:evt:" + key, "1", Duration.ofDays(7));
      if (Boolean.FALSE.equals(ok)) {
        return Map.of("ok", true, "code", "DUPLICATE", "remaining", stock.getOrDefault(sku, new AtomicInteger(0)).get());
      }
    }
    AtomicInteger q = stock.get(sku);
    if (q == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "sku not found");
    synchronized (q) {
      if (q.get() < qty) {
        return Map.of("ok", false, "code", "INSUFFICIENT", "remaining", q.get(), "message", "not enough stock");
      }
      int left = q.addAndGet(-qty);
      return Map.of("ok", true, "code", "RESERVED", "remaining", left, "message", "");
    }
  }

  @PostMapping("/api/inventory/{sku}/confirm")
  public Map<String, Object> confirm(@PathVariable("sku") String sku, @RequestBody Map<String, Object> body) {
    return Map.of("ok", true, "code", "CONFIRMED", "sku", sku, "orderId", body.getOrDefault("orderId", ""));
  }

  private void sleepChaos() {
    int ms = chaosMs.get();
    if (ms > 0) {
      try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
  }
}
