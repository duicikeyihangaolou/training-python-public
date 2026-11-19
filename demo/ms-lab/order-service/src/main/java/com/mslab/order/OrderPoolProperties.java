package com.mslab.order;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * 连接池参数（讲义 §3.2.2）。
 * 值来自 Nacos DataId order-service.yaml 的 order.pool.*；@RefreshScope 保证发布配置后热刷新，无需重启。
 * 默认值仅在 Nacos 不可达时生效。
 */
@Component
@RefreshScope
@ConfigurationProperties(prefix = "order.pool")
public class OrderPoolProperties {
  private int maxSize = 20;
  private int minIdle = 5;

  public int getMaxSize() {
    return maxSize;
  }

  public void setMaxSize(int maxSize) {
    this.maxSize = maxSize;
  }

  public int getMinIdle() {
    return minIdle;
  }

  public void setMinIdle(int minIdle) {
    this.minIdle = minIdle;
  }
}
