package com.investment.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.investment.service.InvestmentApiService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * API Controller
 * Proxies requests to Python backend and provides frontend API
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
@CrossOrigin(origins = "*", allowCredentials = "false")
public class ApiController {

    private final InvestmentApiService investmentApiService;

    @GetMapping("/auth-status")
    public Mono<ResponseEntity<JsonNode>> getAuthStatus() {
        log.info("Getting auth status");
        return investmentApiService.getAuthStatus()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/zerodha-login-url")
    public Mono<ResponseEntity<JsonNode>> getZerodhaLoginUrl() {
        log.info("Getting Zerodha login URL");
        return investmentApiService.getZerodhaLoginUrl()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/exchange-token")
    public Mono<ResponseEntity<JsonNode>> exchangeToken(@RequestBody Map<String, String> request) {
        String requestToken = request.get("request_token");
        log.info("Exchanging token: {}", requestToken != null ? requestToken.substring(0, Math.min(10, requestToken.length())) + "..." : "null");
        return investmentApiService.exchangeToken(requestToken)
                .map(ResponseEntity::ok);
    }

    @PostMapping("/auto-authenticate")
    public Mono<ResponseEntity<JsonNode>> autoAuthenticate() {
        log.info("Triggering automatic authentication");
        return investmentApiService.autoAuthenticate()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/status")
    public Mono<ResponseEntity<JsonNode>> getInvestmentStatus() {
        log.info("Getting investment status");
        return investmentApiService.getInvestmentStatus()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/requirements")
    public Mono<ResponseEntity<JsonNode>> getInvestmentRequirements() {
        log.info("Getting investment requirements");
        return investmentApiService.getInvestmentRequirements()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/calculate-plan")
    public Mono<ResponseEntity<JsonNode>> calculateInvestmentPlan(@RequestBody Map<String, Object> request) {
        log.info("Received calculate investment plan request: {}", request);
        
        Object amountObj = request.get("investment_amount");
        Double amount;
        
        if (amountObj instanceof Number) {
            amount = ((Number) amountObj).doubleValue();
        } else if (amountObj instanceof String) {
            try {
                amount = Double.parseDouble((String) amountObj);
            } catch (NumberFormatException e) {
                log.error("Invalid investment amount format: {}", amountObj);
                return Mono.just(ResponseEntity.badRequest().build());
            }
        } else {
            log.error("Invalid investment amount type: {}", amountObj != null ? amountObj.getClass() : "null");
            return Mono.just(ResponseEntity.badRequest().build());
        }
        
        log.info("Calculating investment plan for amount: {}", amount);
        return investmentApiService.calculateInvestmentPlan(amount)
                .map(ResponseEntity::ok)
                .onErrorResume(error -> {
                    log.error("Error calculating investment plan: ", error);
                    return Mono.just(ResponseEntity.internalServerError().build());
                });
    }

    @PostMapping("/investment/execute-initial")
    public Mono<ResponseEntity<JsonNode>> executeInitialInvestment(@RequestBody Map<String, Double> request) {
        Double amount = request.get("investment_amount");
        log.info("Executing initial investment for amount: {}", amount);
        return investmentApiService.executeInitialInvestment(amount)
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/portfolio-status")
    public Mono<ResponseEntity<JsonNode>> getPortfolioStatus() {
        log.info("Getting portfolio status");
        return investmentApiService.getPortfolioStatus()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/system-orders")
    public Mono<ResponseEntity<JsonNode>> getSystemOrders() {
        log.info("Getting system orders");
        return investmentApiService.getSystemOrders()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/csv-stocks")
    public Mono<ResponseEntity<JsonNode>> getCsvStocks() {
        log.info("Getting CSV stocks");
        return investmentApiService.getCsvStocks()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/force-csv-refresh")
    public Mono<ResponseEntity<JsonNode>> forceCsvRefresh() {
        log.info("Forcing CSV refresh");
        return investmentApiService.forceCsvRefresh()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/calculate-rebalancing")
    public Mono<ResponseEntity<JsonNode>> calculateRebalancing(@RequestBody(required = false) Map<String, Object> request) {
        Double additionalInvestment = 0.0;
        if (request != null && request.containsKey("additional_investment")) {
            Object amountObj = request.get("additional_investment");
            if (amountObj instanceof Number) {
                additionalInvestment = ((Number) amountObj).doubleValue();
            }
        }
        log.info("Calculating rebalancing with additional investment: {}", additionalInvestment);
        return investmentApiService.calculateRebalancing(additionalInvestment)
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/execute-rebalancing")
    public Mono<ResponseEntity<JsonNode>> executeRebalancing(@RequestBody(required = false) Map<String, Object> request) {
        Double additionalInvestment = 0.0;
        if (request != null && request.containsKey("additional_investment")) {
            Object amountObj = request.get("additional_investment");
            if (amountObj instanceof Number) {
                additionalInvestment = ((Number) amountObj).doubleValue();
            }
        }
        log.info("Executing rebalancing with additional investment: {}", additionalInvestment);
        return investmentApiService.executeRebalancing(additionalInvestment)
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/reset-orders")
    public Mono<ResponseEntity<JsonNode>> resetSystemOrders() {
        log.info("Resetting system orders");
        return investmentApiService.resetSystemOrders()
                .map(ResponseEntity::ok);
    }

    @GetMapping("/investment/failed-orders")
    public Mono<ResponseEntity<JsonNode>> getFailedOrders() {
        log.info("Getting failed orders");
        return investmentApiService.getFailedOrders()
                .map(ResponseEntity::ok);
    }

    @PostMapping("/investment/retry-orders")
    public Mono<ResponseEntity<JsonNode>> retryFailedOrders(@RequestBody(required = false) Map<String, Object> request) {
        java.util.List<Integer> orderIds = null;
        if (request != null && request.containsKey("order_ids")) {
            Object orderIdsObj = request.get("order_ids");
            if (orderIdsObj instanceof java.util.List) {
                orderIds = (java.util.List<Integer>) orderIdsObj;
            }
        }
        log.info("Retrying failed orders: {}", orderIds != null ? orderIds : "all");
        return investmentApiService.retryFailedOrders(orderIds)
                .map(ResponseEntity::ok);
    }

    @GetMapping("/health")
    public Mono<ResponseEntity<JsonNode>> getHealthStatus() {
        log.info("Getting health status");
        return investmentApiService.getHealthStatus()
                .map(ResponseEntity::ok);
    }
}