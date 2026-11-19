package com.mslab.order;

import feign.Request;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

@Configuration
public class FeignConfig {
  @Bean
  public Request.Options options() {
    return new Request.Options(200, TimeUnit.MILLISECONDS, 800, TimeUnit.MILLISECONDS, true);
  }
}
