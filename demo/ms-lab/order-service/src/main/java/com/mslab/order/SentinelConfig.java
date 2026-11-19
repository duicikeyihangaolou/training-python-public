package com.mslab.order;

import com.alibaba.csp.sentinel.annotation.aspectj.SentinelResourceAspect;
import com.alibaba.csp.sentinel.slots.block.RuleConstant;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeRule;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeRuleManager;
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Collections;

@Configuration
public class SentinelConfig {
  @Bean
  public SentinelResourceAspect sentinelResourceAspect() {
    return new SentinelResourceAspect();
  }

  @PostConstruct
  public void initRules() {
    DegradeRule rule = new DegradeRule("createOrder")
        .setGrade(RuleConstant.DEGRADE_GRADE_RT)
        .setCount(500)
        .setTimeWindow(8)
        .setMinRequestAmount(5)
        .setStatIntervalMs(1000)
        .setSlowRatioThreshold(0.5);
    DegradeRuleManager.loadRules(Collections.singletonList(rule));
  }
}
