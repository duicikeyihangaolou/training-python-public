package com.mslab.order;

import jakarta.persistence.*;

@Entity
@Table(name = "outbox")
public class OutboxEntity {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  public Long id;
  @Column(unique = true)
  public String eventId;
  public String aggregateId;
  public String eventType;
  @Lob
  public String payload;
  public String status;
}
