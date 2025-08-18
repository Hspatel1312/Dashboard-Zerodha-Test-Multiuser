package com.investment.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * Main Controller
 * Handles routing for the React SPA
 */
@Controller
public class MainController {

    @GetMapping("/")
    public String index() {
        return "forward:/index.html";
    }

    @GetMapping("/dashboard")
    public String dashboard() {
        return "forward:/index.html";
    }

    @GetMapping("/portfolio")
    public String portfolio() {
        return "forward:/index.html";
    }

    @GetMapping("/orders")
    public String orders() {
        return "forward:/index.html";
    }

    @GetMapping("/stocks")
    public String stocks() {
        return "forward:/index.html";
    }

    @GetMapping("/settings")
    public String settings() {
        return "forward:/index.html";
    }
}