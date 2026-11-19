package com.mslab.gateway;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;

@RestController
public class AuthController {
  private final JwtSupport jwt;

  public AuthController(JwtSupport jwt) {
    this.jwt = jwt;
  }

  @GetMapping(value = "/health", produces = MediaType.APPLICATION_JSON_VALUE)
  public Mono<Map<String, Object>> health() {
    return Mono.just(Map.of("ok", true, "service", "gateway"));
  }

  @PostMapping(value = "/public/token", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
  public Mono<Map<String, Object>> token(@RequestBody Map<String, String> body) {
    String userId = body.getOrDefault("userId", body.getOrDefault("user_id", "u1"));
    return Mono.just(Map.of("access_token", jwt.issue(userId), "token_type", "Bearer", "userId", userId));
  }
}
