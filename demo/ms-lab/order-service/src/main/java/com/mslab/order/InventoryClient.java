package com.mslab.order;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@FeignClient(
    name = "inventory-service",
    url = "${inventory.confirm-url:}",
    fallbackFactory = InventoryFallbackFactory.class)
public interface InventoryClient {
  @PostMapping("/api/inventory/{sku}/reserve")
  Map<String, Object> reserve(@PathVariable("sku") String sku,
                              @RequestBody Map<String, Object> body,
                              @RequestHeader("X-Idempotency-Key") String idem);
}
