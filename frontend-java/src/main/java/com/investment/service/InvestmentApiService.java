package com.investment.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

/**
 * Service to communicate with Python backend API
 * Handles all API calls to the investment backend
 */
@Service
@Slf4j
public class InvestmentApiService {

    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    public InvestmentApiService(@Value("${investment.backend.url:http://127.0.0.1:8000}") String backendUrl,
                               WebClient.Builder webClientBuilder,
                               ObjectMapper objectMapper) {
        this.webClient = webClientBuilder
                .baseUrl(backendUrl)
                .build();
        this.objectMapper = objectMapper;
    }

    /**
     * Check Zerodha authentication status
     */
    public Mono<JsonNode> getAuthStatus() {
        return webClient.get()
                .uri("/api/auth-status")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(10))
                .onErrorResume(this::handleError);
    }

    /**
     * Get Zerodha login URL
     */
    public Mono<JsonNode> getZerodhaLoginUrl() {
        return webClient.get()
                .uri("/auth/zerodha-login-url")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(10))
                .onErrorResume(this::handleError);
    }

    /**
     * Exchange request token for access token
     */
    public Mono<JsonNode> exchangeToken(String requestToken) {
        Map<String, String> request = Map.of("request_token", requestToken);
        
        return webClient.post()
                .uri("/auth/exchange-token")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(15))
                .onErrorResume(this::handleError);
    }

    /**
     * Trigger automatic authentication
     */
    public Mono<JsonNode> autoAuthenticate() {
        return webClient.post()
                .uri("/api/auto-auth")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(20))
                .onErrorResume(this::handleError);
    }

    /**
     * Get investment status
     */
    public Mono<JsonNode> getInvestmentStatus() {
        return webClient.get()
                .uri("/api/investment/status")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Get investment requirements
     */
    public Mono<JsonNode> getInvestmentRequirements() {
        return webClient.get()
                .uri("/api/investment/requirements")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Calculate investment plan
     */
    public Mono<JsonNode> calculateInvestmentPlan(double amount) {
        Map<String, Double> request = Map.of("investment_amount", amount);
        
        return webClient.post()
                .uri("/api/investment/calculate-plan")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Execute initial investment
     */
    public Mono<JsonNode> executeInitialInvestment(double amount) {
        Map<String, Double> request = Map.of("investment_amount", amount);
        
        return webClient.post()
                .uri("/api/investment/execute-initial")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(45))
                .onErrorResume(this::handleError);
    }

    /**
     * Get portfolio status
     */
    public Mono<JsonNode> getPortfolioStatus() {
        return webClient.get()
                .uri("/api/investment/portfolio-status")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Get system orders
     */
    public Mono<JsonNode> getSystemOrders() {
        return webClient.get()
                .uri("/api/investment/system-orders")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(15))
                .onErrorResume(this::handleError);
    }

    /**
     * Get CSV stocks
     */
    public Mono<JsonNode> getCsvStocks() {
        return webClient.get()
                .uri("/api/investment/csv-stocks")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Force CSV refresh
     */
    public Mono<JsonNode> forceCsvRefresh() {
        return webClient.post()
                .uri("/api/investment/force-csv-refresh")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Calculate rebalancing plan
     */
    public Mono<JsonNode> calculateRebalancing(double additionalInvestment) {
        Map<String, Double> request = Map.of("additional_investment", additionalInvestment);
        
        return webClient.post()
                .uri("/api/investment/calculate-rebalancing")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(45))
                .onErrorResume(this::handleError);
    }

    /**
     * Execute rebalancing
     */
    public Mono<JsonNode> executeRebalancing(double additionalInvestment) {
        Map<String, Double> request = Map.of("additional_investment", additionalInvestment);
        
        return webClient.post()
                .uri("/api/investment/execute-rebalancing")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(60))
                .onErrorResume(this::handleError);
    }

    /**
     * Get health status
     */
    public Mono<JsonNode> getHealthStatus() {
        return webClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(15))
                .onErrorResume(this::handleError);
    }

    /**
     * Reset system orders (for testing)
     */
    public Mono<JsonNode> resetSystemOrders() {
        return webClient.post()
                .uri("/api/investment/reset-orders")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(15))
                .onErrorResume(this::handleError);
    }

    /**
     * Get failed orders
     */
    public Mono<JsonNode> getFailedOrders() {
        return webClient.get()
                .uri("/api/investment/failed-orders")
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(15))
                .onErrorResume(this::handleError);
    }

    /**
     * Retry failed orders
     */
    public Mono<JsonNode> retryFailedOrders(java.util.List<Integer> orderIds) {
        Map<String, Object> request = new java.util.HashMap<>();
        request.put("order_ids", orderIds); // null means retry all
        
        return webClient.post()
                .uri("/api/investment/retry-orders")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorResume(this::handleError);
    }

    /**
     * Handle API errors
     */
    private Mono<JsonNode> handleError(Throwable error) {
        log.error("API call failed", error);
        
        JsonNode errorResponse;
        try {
            if (error instanceof WebClientResponseException webEx) {
                errorResponse = objectMapper.createObjectNode()
                        .put("success", false)
                        .put("error", "API Error: " + webEx.getStatusCode())
                        .put("message", webEx.getResponseBodyAsString());
            } else {
                errorResponse = objectMapper.createObjectNode()
                        .put("success", false)
                        .put("error", "Connection Error")
                        .put("message", error.getMessage());
            }
        } catch (Exception e) {
            errorResponse = objectMapper.createObjectNode()
                    .put("success", false)
                    .put("error", "Unknown Error")
                    .put("message", "Failed to process error response");
        }
        
        return Mono.just(errorResponse);
    }
}