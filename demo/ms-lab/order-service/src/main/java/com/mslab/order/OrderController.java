package com.mslab.order;

import com.alibaba.csp.sentinel.annotation.SentinelResource;
import com.alibaba.csp.sentinel.slots.block.BlockException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
public class OrderController {
  private final UserClient userClient;
  private final InventoryClient inventoryClient;
  private final OrderRepo orderRepo;
  private final OutboxRepo outboxRepo;
  private final OrderPoolProperties poolProps;
  private final ObjectMapper om = new ObjectMapper();
  private final Counter okCounter;
  private final Counter errCounter;

  public OrderController(UserClient userClient, InventoryClient inventoryClient,
                         OrderRepo orderRepo, OutboxRepo outboxRepo,
                         OrderPoolProperties poolProps, MeterRegistry registry) {
    this.userClient = userClient;
    this.inventoryClient = inventoryClient;
    this.orderRepo = orderRepo;
    this.outboxRepo = outboxRepo;
    this.poolProps = poolProps;
    this.okCounter = Counter.builder("orders_total").tag("status", "ok").register(registry);
    this.errCounter = Counter.builder("orders_total").tag("status", "error").register(registry);
  }

  @GetMapping("/health")
  public Map<String, Object> health() {
    return Map.of("ok", true, "service", "order-service",
        "pool", Map.of("maxSize", poolProps.getMaxSize(), "minIdle", poolProps.getMinIdle()));
  }

  /** 离线兜底：不经过 Nacos，直接改当前 Pod 内的池参数（重启后回到 Nacos 配置）。 */
  @PostMapping("/admin/reload")
  public Map<String, Object> reload(@RequestBody Map<String, Object> body) {
    if (body.containsKey("maxSize")) {
      poolProps.setMaxSize(((Number) body.get("maxSize")).intValue());
    }
    return Map.of("pool", Map.of("maxSize", poolProps.getMaxSize(), "minIdle", poolProps.getMinIdle()));
  }

  @GetMapping("/api/orders/{id}")
  public OrderEntity get(@PathVariable("id") String id) {
    return orderRepo.findById(id).orElseThrow();
  }

  @PostMapping("/api/orders")
  @SentinelResource(value = "createOrder", blockHandler = "createOrderBlocked")
  @Transactional
  public Map<String, Object> create(@RequestBody Map<String, Object> req) throws Exception {
    String userId = String.valueOf(req.get("userId"));
    String sku = String.valueOf(req.getOrDefault("sku", "sku-1"));
    int qty = ((Number) req.getOrDefault("qty", 1)).intValue();
    try {
      userClient.get(userId);
    } catch (Exception e) {
      errCounter.increment();
      return Map.of("ok", false, "code", "INVALID_USER", "message", e.toString(), "degraded", true);
    }
    String orderId = "O" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
    Map<String, Object> reserve;
    try {
      reserve = inventoryClient.reserve(sku,
          Map.of("orderId", orderId, "qty", qty, "eventId", "reserve-" + orderId),
          "reserve-" + orderId);
    } catch (Exception e) {
      // Feign 超时/Sentinel 未挂上 Fallback 时仍返回非 null 降级体
      reserve = Map.of(
          "ok", false,
          "code", "INVENTORY_UNAVAILABLE",
          "message", e.toString(),
          "degraded", true);
    }
    if (reserve == null) {
      reserve = Map.of("ok", false, "code", "INVENTORY_UNAVAILABLE", "message", "null fallback", "degraded", true);
    }
    if (!Boolean.TRUE.equals(reserve.get("ok"))) {
      errCounter.increment();
      return Map.of(
          "ok", false,
          "code", String.valueOf(reserve.getOrDefault("code", "INVENTORY_UNAVAILABLE")),
          "message", String.valueOf(reserve.getOrDefault("message", "")),
          "degraded", true,
          "inventory", reserve);
    }
    OrderEntity o = new OrderEntity();
    o.id = orderId; o.userId = userId; o.sku = sku; o.qty = qty;
    o.amountCents = qty * 1000; o.status = "CREATED";
    orderRepo.save(o);
    OutboxEntity ox = new OutboxEntity();
    ox.eventId = "evt-" + orderId;
    ox.aggregateId = orderId;
    ox.eventType = "OrderCreated";
    ox.payload = om.writeValueAsString(Map.of(
        "eventId", ox.eventId, "orderId", orderId, "userId", userId, "sku", sku, "qty", qty));
    ox.status = "NEW";
    outboxRepo.save(ox);
    okCounter.increment();
    return Map.of("ok", true, "code", "CREATED", "orderId", orderId,
        "amountCents", o.amountCents, "inventory", reserve,
        "pool", Map.of("maxSize", poolProps.getMaxSize(), "minIdle", poolProps.getMinIdle()));
  }

  public Map<String, Object> createOrderBlocked(Map<String, Object> req, BlockException ex) {
    errCounter.increment();
    return Map.of("ok", false, "code", "ORDER_DEGRADED", "message", "sentinel blocked: " + ex.getClass().getSimpleName(),
        "degraded", true);
  }
}
