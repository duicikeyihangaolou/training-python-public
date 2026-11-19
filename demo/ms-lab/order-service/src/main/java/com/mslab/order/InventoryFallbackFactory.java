package com.mslab.order;

import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class InventoryFallbackFactory implements FallbackFactory<InventoryClient> {
  @Override
  public InventoryClient create(Throwable cause) {
    return (sku, body, idem) -> Map.of(
        "ok", false,
        "code", "INVENTORY_UNAVAILABLE",
        "message", cause == null ? "fallback" : cause.toString(),
        "degraded", true
    );
  }
}
