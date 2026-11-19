package com.mslab.gateway;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class AuthHeaderFilter implements GlobalFilter, Ordered {
  private final JwtSupport jwt;

  @Value("${canary.percent:10}")
  private int canaryPercent;

  public AuthHeaderFilter(JwtSupport jwt) {
    this.jwt = jwt;
  }

  @Override
  public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
    String path = exchange.getRequest().getURI().getPath();
    if (path.startsWith("/public/") || path.equals("/health") || path.startsWith("/actuator")) {
      return chain.filter(exchange);
    }
    String auth = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
    if (auth == null || !auth.startsWith("Bearer ")) {
      exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
      return exchange.getResponse().setComplete();
    }
    try {
      String userId = jwt.subject(auth.substring(7));
      HttpHeaders in = exchange.getRequest().getHeaders();
      String canaryHdr = in.getFirst("X-Canary");
      String expHdr = in.getFirst("X-Experiment");
      boolean canary = canaryHdr != null
          ? "true".equalsIgnoreCase(canaryHdr)
          : Math.floorMod(userId.hashCode(), 100) < canaryPercent;
      String exp = expHdr != null ? expHdr
          : (Math.floorMod((userId + ":exp").hashCode(), 100) < 50 ? "ranker_v1" : "ranker_v2");
      ServerHttpRequest req = exchange.getRequest().mutate()
          .header("X-User-Id", userId)
          .header("X-Canary", canary ? "true" : "false")
          .header("X-Experiment", exp)
          .build();
      return chain.filter(exchange.mutate().request(req).build());
    } catch (Exception e) {
      exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
      return exchange.getResponse().setComplete();
    }
  }

  @Override
  public int getOrder() {
    return -100;
  }
}
