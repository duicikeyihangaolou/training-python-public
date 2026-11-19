package com.mslab.order;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.Map;

@FeignClient(name = "user-service", url = "${user.base-url:http://user-service:8080}")
public interface UserClient {
  @GetMapping("/api/users/{userId}")
  Map<String, Object> get(@PathVariable("userId") String userId);
}
