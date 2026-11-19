package com.mslab.order;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Component
public class OutboxWorker {
  private final OutboxRepo outboxRepo;
  private final StringRedisTemplate redis;
  private final RestTemplate http = new RestTemplate();
  private final ObjectMapper om = new ObjectMapper();

  @Value("${inventory.confirm-url:http://inventory-service:8080}")
  private String inventoryBase;

  public OutboxWorker(OutboxRepo outboxRepo, StringRedisTemplate redis) {
    this.outboxRepo = outboxRepo;
    this.redis = redis;
  }

  @Scheduled(fixedDelay = 1000)
  public void flush() {
    List<OutboxEntity> rows = outboxRepo.findTop20ByStatusOrderByIdAsc("NEW");
    for (OutboxEntity row : rows) {
      try {
        redis.opsForStream().add("order.created", Map.of("payload", row.payload));
        @SuppressWarnings("unchecked")
        Map<String, Object> data = om.readValue(row.payload, Map.class);
        String sku = String.valueOf(data.getOrDefault("sku", "sku-1"));
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        http.postForEntity(inventoryBase + "/api/inventory/" + sku + "/confirm",
            new HttpEntity<>(data, headers), Map.class);
        row.status = "SENT";
        outboxRepo.save(row);
      } catch (Exception e) {
        System.out.println("outbox error: " + e);
      }
    }
  }
}
