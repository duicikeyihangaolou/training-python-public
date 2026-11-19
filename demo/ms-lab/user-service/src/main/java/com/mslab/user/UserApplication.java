package com.mslab.user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@SpringBootApplication
@RestController
public class UserApplication {
  private static final Map<String, Map<String, Object>> USERS = new ConcurrentHashMap<>();
  static {
    for (int i = 1; i <= 100; i++) {
      String id = "u" + i;
      USERS.put(id, Map.of("userId", id, "name", "User" + i, "status", i == 3 ? "blocked" : "active"));
    }
  }

  public static void main(String[] args) {
    SpringApplication.run(UserApplication.class, args);
  }

  @GetMapping("/health")
  public Map<String, Object> health() {
    return Map.of("ok", true, "service", "user-service");
  }

  @GetMapping("/api/users/{userId}")
  public Map<String, Object> get(@PathVariable("userId") String userId) {
    Map<String, Object> u = USERS.get(userId);
    if (u == null || !"active".equals(u.get("status"))) {
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "user not found or blocked");
    }
    return u;
  }
}
