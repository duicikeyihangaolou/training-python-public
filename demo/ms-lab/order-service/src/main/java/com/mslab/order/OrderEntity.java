package com.mslab.order;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "orders")
public class OrderEntity {
  @Id
  public String id;
  public String userId;
  public String sku;
  public int qty;
  public int amountCents;
  public String status;
}
