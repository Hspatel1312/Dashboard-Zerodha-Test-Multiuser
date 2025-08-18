package com.investment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.web.socket.config.annotation.EnableWebSocket;

/**
 * Investment Dashboard Application
 * Premium UI for Investment Rebalancing
 */
@SpringBootApplication
@EnableWebSocket
@EnableConfigurationProperties
public class InvestmentDashboardApplication {

    public static void main(String[] args) {
        SpringApplication.run(InvestmentDashboardApplication.class, args);
    }
}