# backend/app/services/investment_calculator.py
from typing import Dict, List, Tuple
import math

# Foundation imports
from .base.base_service import BaseService
from .utils.financial_calculations import FinancialCalculations, InvestmentValidation
from .utils.error_handler import ErrorHandler
from .utils.config import InvestmentConfig
from .utils.logger import LoggerFactory

class InvestmentCalculator(BaseService):
    def __init__(self):
        BaseService.__init__(self, service_name="investment_calculator")
        
        # Use configuration from InvestmentConfig
        self.default_min_allocation_percent = 3.0  # 5% - 2% = 3.0%
        self.default_target_allocation_percent = InvestmentConfig.DEFAULT_TARGET_ALLOCATION_PERCENT
        self.default_max_allocation_percent = 7.0  # 5% + 2% = 7.0%
        
        # Flexibility settings
        self.allocation_flexibility_percent = 2.0  # ±2% flexibility
        
        # GOLDBEES allocation settings
        self.goldbees_allocation_percent = InvestmentConfig.GOLDBEES_ALLOCATION_PERCENT
        self.goldbees_symbol = "GOLDBEES"
    
    def _detect_goldbees_and_calculate_allocations(self, stocks_data: List[Dict]) -> Dict:
        """
        Detect if GOLDBEES is present and calculate allocation percentages
        """
        has_goldbees = any(stock.get('symbol') == self.goldbees_symbol for stock in stocks_data)
        
        if has_goldbees:
            # GOLDBEES present: 50% to GOLDBEES, remaining 50% equally among other stocks
            non_goldbees_stocks = len([stock for stock in stocks_data if stock.get('symbol') != self.goldbees_symbol])
            remaining_allocation = 100.0 - self.goldbees_allocation_percent  # 50%
            
            if non_goldbees_stocks == 0:
                # Only GOLDBEES - give it 100%
                target_allocation_per_stock = self.goldbees_allocation_percent
                min_allocation_per_stock = self.goldbees_allocation_percent - self.allocation_flexibility_percent
                max_allocation_per_stock = self.goldbees_allocation_percent + self.allocation_flexibility_percent
            else:
                # Normal case: other stocks get equal share of remaining 50%
                target_allocation_per_stock = remaining_allocation / non_goldbees_stocks  # e.g., 50% / 19 stocks = 2.63% each
                min_allocation_per_stock = max(0.5, target_allocation_per_stock - self.allocation_flexibility_percent)
                max_allocation_per_stock = target_allocation_per_stock + self.allocation_flexibility_percent
            
            return {
                'has_goldbees': True,
                'goldbees_allocation': self.goldbees_allocation_percent,
                'target_allocation_per_stock': target_allocation_per_stock,
                'min_allocation_per_stock': min_allocation_per_stock,
                'max_allocation_per_stock': max_allocation_per_stock,
                'non_goldbees_stocks': non_goldbees_stocks,
                'allocation_strategy': f"GOLDBEES: {self.goldbees_allocation_percent}%, Others: {target_allocation_per_stock:.2f}% each"
            }
        else:
            # No GOLDBEES: equal allocation for all stocks
            target_allocation_per_stock = 100.0 / len(stocks_data)  # e.g., 100% / 20 = 5% each
            
            return {
                'has_goldbees': False,
                'goldbees_allocation': 0,
                'target_allocation_per_stock': target_allocation_per_stock,
                'min_allocation_per_stock': max(0.5, target_allocation_per_stock - self.allocation_flexibility_percent),
                'max_allocation_per_stock': target_allocation_per_stock + self.allocation_flexibility_percent,
                'non_goldbees_stocks': len(stocks_data),
                'allocation_strategy': f"Equal weight: {target_allocation_per_stock:.2f}% each (±{self.allocation_flexibility_percent}%)"
            }
    
    def calculate_minimum_investment(self, stocks_data: List[Dict]) -> Dict:
        """
        Calculate minimum investment required using MAXIMUM allocation approach
        - Uses most expensive stock at maximum allocation (±2% flexibility)
        - GOLDBEES scenario: 2.5% + 2% = 4.5% max allocation
        - No GOLDBEES scenario: 5% + 2% = 7% max allocation
        STRICT: Only works with REAL price data
        """
        with self.handle_operation_error("calculate_minimum_investment"):
            self.logger.info(f"Calculating minimum investment for {len(stocks_data)} stocks...")
            
            if not stocks_data:
                raise Exception("No stocks data provided")
            
            # Validate stock prices using InvestmentValidation
            invalid_stocks = InvestmentValidation.validate_stock_prices(stocks_data)
            if invalid_stocks:
                raise Exception(f"PRICE_DATA_INVALID: Found {len(invalid_stocks)} stocks without valid live prices: {', '.join(invalid_stocks[:5])}")
            
            # Detect GOLDBEES and calculate dynamic allocations
            allocation_info = self._detect_goldbees_and_calculate_allocations(stocks_data)
            self.logger.info(f"Allocation strategy: {allocation_info['allocation_strategy']}")
            
            # NEW APPROACH: Use MAXIMUM allocation to find minimum investment
            if allocation_info['has_goldbees']:
                # For GOLDBEES scenario, use most expensive regular stock at maximum allocation
                non_goldbees_stocks = [stock for stock in stocks_data if stock.get('symbol') != self.goldbees_symbol]
                
                if non_goldbees_stocks:
                    # Find most expensive regular stock
                    most_expensive_regular = max(non_goldbees_stocks, key=lambda x: x['price'])
                    
                    # Use MAXIMUM allocation for the most expensive stock to minimize investment
                    max_allocation_percent = allocation_info['max_allocation_per_stock']  # e.g., 4.5%
                    price = most_expensive_regular['price']
                    min_investment_required = price * (100 / max_allocation_percent)
                    most_expensive_stock = most_expensive_regular
                    
                    print(f"   Most expensive stock: {most_expensive_regular['symbol']} at Rs.{most_expensive_regular['price']:,.2f}")
                    print(f"   Using maximum allocation: {max_allocation_percent:.1f}%")
                    print(f"   Minimum investment: Rs.{min_investment_required:,.0f}")
                else:
                    # Only GOLDBEES case
                    goldbees_stock = next((stock for stock in stocks_data if stock.get('symbol') == self.goldbees_symbol), None)
                    max_goldbees_allocation = self.goldbees_allocation_percent + self.allocation_flexibility_percent
                    min_investment_required = goldbees_stock['price'] * (100 / max_goldbees_allocation)
                    most_expensive_stock = goldbees_stock
            else:
                # No GOLDBEES: use most expensive stock at maximum allocation
                most_expensive_stock = max(stocks_data, key=lambda x: x['price'])
                max_allocation_percent = allocation_info['max_allocation_per_stock']  # e.g., 7.0%
                min_investment_required = most_expensive_stock['price'] * (100 / max_allocation_percent)
            
            max_price = most_expensive_stock['price']
            print(f"   Critical stock: {most_expensive_stock['symbol']} at Rs.{max_price:,.2f} (LIVE)")
            
            # Add buffer to ensure all stocks can get close to 5% allocation
            buffer_percent = 20  # 20% buffer
            recommended_minimum = min_investment_required * (1 + buffer_percent / 100)
            
            # Calculate details for each stock using dynamic allocations
            stock_details = []
            for stock in stocks_data:
                symbol = stock['symbol']
                price = stock['price']
                # Safety check: ensure price is always a number
                if isinstance(price, dict):
                    price = price.get('price', price.get('last_price', 0))
                price = float(price) if price else 0
                
                # Use different allocation based on whether it's GOLDBEES or regular stock
                if symbol == self.goldbees_symbol and allocation_info['has_goldbees']:
                    min_allocation = self.goldbees_allocation_percent - self.allocation_flexibility_percent  # 48%
                    max_allocation = self.goldbees_allocation_percent + self.allocation_flexibility_percent  # 52%
                    target_allocation = self.goldbees_allocation_percent  # 50%
                else:
                    min_allocation = allocation_info['min_allocation_per_stock']
                    max_allocation = allocation_info['max_allocation_per_stock']
                    target_allocation = allocation_info['target_allocation_per_stock']
                
                # Use MAXIMUM allocation for minimum investment calculation (new approach)
                min_investment_for_stock = price * (100 / max_allocation)
                
                stock_details.append({
                    'symbol': symbol,
                    'price': price,
                    'price_type': 'LIVE',
                    'min_investment_for_allocation': min_investment_for_stock,
                    'target_allocation_percent': target_allocation,
                    'min_allocation_percent': min_allocation,
                    'max_allocation_percent': max_allocation,
                    'min_shares': 1,
                    'is_goldbees': symbol == self.goldbees_symbol
                })
                
                print(f"   {symbol}: Rs.{price:.2f}/share (LIVE) - Target: {target_allocation:.2f}% - Min investment: Rs.{min_investment_for_stock:,.0f}")
            
            result = {
                'minimum_investment': min_investment_required,
                'recommended_minimum': recommended_minimum,
                'buffer_percent': buffer_percent,
                'total_stocks': len(stock_details),
                'valid_stocks': len(stock_details),
                'invalid_stocks': 0,
                'stock_details': stock_details,
                'most_expensive_stock': most_expensive_stock,
                'allocation_info': allocation_info,
                'calculation_basis': f"Based on {allocation_info['allocation_strategy']} - Critical stock: {most_expensive_stock['symbol']}",
                'data_quality': 'HIGH - All prices from live API'
            }
            
            print(f"[SUCCESS] Minimum investment calculated with LIVE data:")
            print(f"   Absolute minimum: Rs.{min_investment_required:,.0f}")
            print(f"   Recommended minimum: Rs.{recommended_minimum:,.0f}")
            print(f"   Data quality: HIGH - All live prices")
            
            self.logger.success(f"Minimum investment calculation complete")
            return result
    
    def calculate_optimal_allocation(self, investment_amount: float, stocks_data: List[Dict]) -> Dict:
        """
        Calculate optimal allocation using sophisticated algorithm
        STRICT: Only works with REAL price data
        """
        with self.handle_operation_error("calculate_optimal_allocation"):
            self.logger.info(f"Calculating optimal allocation for Rs.{investment_amount:,.0f}")
            
            # Detect GOLDBEES and calculate dynamic allocations
            allocation_info = self._detect_goldbees_and_calculate_allocations(stocks_data)
            print(f"   {allocation_info['allocation_strategy']}")
            
            # Validate stock prices using InvestmentValidation
            invalid_stocks = InvestmentValidation.validate_stock_prices(stocks_data)
            if invalid_stocks:
                raise Exception(f"PRICE_DATA_INVALID: Found {len(invalid_stocks)} stocks without valid live prices: {', '.join(invalid_stocks[:5])}")
            
            # Phase 1: Initial allocation using dynamic targets
            allocations = []
            total_allocated = 0
            
            print(f"[INFO] Phase 1: Initial allocation using dynamic targets - ALL LIVE PRICES")
            
            for stock in stocks_data:
                symbol = stock['symbol']
                price = stock['price']
                # Safety check: ensure price is always a number
                if isinstance(price, dict):
                    price = price.get('price', price.get('last_price', 0))
                price = float(price) if price else 0
                
                # Use different allocation targets based on stock type
                if symbol == self.goldbees_symbol and allocation_info['has_goldbees']:
                    # GOLDBEES gets 50% allocation
                    target_allocation_percent = allocation_info['goldbees_allocation']
                    min_allocation_percent = allocation_info['goldbees_allocation'] - 1.5  # 48.5%
                    max_allocation_percent = allocation_info['goldbees_allocation'] + 1.5  # 51.5%
                    
                    print(f"   {symbol} (GOLDBEES): Target {target_allocation_percent}% allocation")
                else:
                    # Regular stocks get equal share of remaining allocation
                    target_allocation_percent = allocation_info['target_allocation_per_stock']
                    min_allocation_percent = allocation_info['min_allocation_per_stock']
                    max_allocation_percent = allocation_info['max_allocation_per_stock']
                
                # Calculate target investment amount for this stock
                target_per_stock = investment_amount * (target_allocation_percent / 100)
                min_value = investment_amount * (min_allocation_percent / 100)
                max_value = investment_amount * (max_allocation_percent / 100)
                
                min_shares = max(1, math.ceil(min_value / price))  # At least 1 share
                max_shares = math.floor(max_value / price)
                
                # Start with target shares
                target_shares = max(1, math.floor(target_per_stock / price))
                
                # Ensure target is within constraints
                if target_shares < min_shares:
                    optimal_shares = min_shares
                elif target_shares > max_shares:
                    optimal_shares = max_shares
                else:
                    optimal_shares = target_shares
                
                allocation_value = optimal_shares * price
                allocation_percent = (allocation_value / investment_amount) * 100
                
                allocation = {
                    'symbol': symbol,
                    'price': price,
                    'price_type': 'LIVE',
                    'shares': optimal_shares,
                    'value': allocation_value,
                    'allocation_percent': allocation_percent,
                    'target_allocation_percent': target_allocation_percent,
                    'min_shares': min_shares,
                    'max_shares': max_shares,
                    'target_met': abs(allocation_percent - target_allocation_percent) < 0.5,
                    'is_goldbees': symbol == self.goldbees_symbol
                }
                
                allocations.append(allocation)
                total_allocated += allocation_value
                
                print(f"   {symbol}: {optimal_shares} shares × Rs.{price:.2f} (LIVE) = Rs.{allocation_value:,.0f} ({allocation_percent:.2f}%)")
            
            remaining_cash = investment_amount - total_allocated
            print(f"[INFO] After initial allocation: Rs.{remaining_cash:,.0f} remaining")
            
            # Phase 2: Iterative optimization to get closer to 5% for each stock
            if remaining_cash > 0:
                print(f"[INFO] Phase 2: Optimizing allocation with remaining Rs.{remaining_cash:,.0f}")
                remaining_cash = self._optimize_allocation(allocations, remaining_cash, investment_amount)
            
            # Phase 3: Final validation and summary
            final_total = sum(alloc['value'] for alloc in allocations)
            final_remaining = investment_amount - final_total
            
            allocation_summary = {
                'total_investment': investment_amount,
                'total_allocated': final_total,
                'remaining_cash': final_remaining,
                'utilization_percent': (final_total / investment_amount) * 100,
                'allocations': allocations,
                'allocation_info': allocation_info,
                'allocation_stats': self._calculate_allocation_stats(allocations),
                'validation': self._validate_allocations(allocations, investment_amount),
                'data_quality': 'HIGH - All prices from live API'
            }
            
            print(f"[SUCCESS] Optimal allocation calculated with LIVE data:")
            print(f"   Total allocated: Rs.{final_total:,.0f} ({(final_total/investment_amount)*100:.2f}%)")
            print(f"   Remaining cash: Rs.{final_remaining:,.0f}")
            print(f"   Stocks in range: {allocation_summary['validation']['stocks_in_range']}/{len(allocations)}")
            print(f"   Data quality: HIGH - All live prices")
            
            return allocation_summary
    
    def _optimize_allocation(self, allocations: List[Dict], remaining_cash: float, total_investment: float) -> float:
        """
        Sophisticated optimization to distribute remaining cash
        Prioritizes getting stocks closer to 5% target
        """
        
        # Safety check: ensure all allocation prices are numeric
        for alloc in allocations:
            if isinstance(alloc['price'], dict):
                alloc['price'] = alloc['price'].get('price', alloc['price'].get('last_price', 0))
            alloc['price'] = float(alloc['price']) if alloc['price'] else 0
        
        iteration = 0
        max_iterations = 20  # Increased iterations for better optimization
        min_improvement = 100  # Stop if improvement is less than Rs.100
        
        while remaining_cash > min_improvement and iteration < max_iterations:
            iteration += 1
            print(f"   [INFO] Optimization iteration {iteration}: Rs.{remaining_cash:,.0f} to distribute")
            
            # Calculate how far each stock is from target allocation
            candidates = []
            for alloc in allocations:
                current_percent = (alloc['value'] / total_investment) * 100
                target_percent = alloc.get('target_allocation_percent', 5.0)  # Use stock-specific target
                distance_from_target = abs(current_percent - target_percent)
                
                # Check if we can add shares without exceeding max limit for this stock
                max_percent = target_percent + self.allocation_flexibility_percent  # Dynamic max based on target
                max_additional_value = (total_investment * (max_percent / 100)) - alloc['value']
                
                if max_additional_value > alloc['price']:  # Can buy at least 1 more share
                    max_additional_shares = math.floor(max_additional_value / alloc['price'])
                    affordable_shares = math.floor(remaining_cash / alloc['price'])
                    possible_additional_shares = min(max_additional_shares, affordable_shares)
                    
                    if possible_additional_shares > 0:
                        # Calculate what the new allocation would be
                        new_value = alloc['value'] + (possible_additional_shares * alloc['price'])
                        new_percent = (new_value / total_investment) * 100
                        new_distance = abs(new_percent - target_percent)
                        
                        # Only consider if it improves the allocation
                        if new_distance < distance_from_target:
                            improvement_score = distance_from_target - new_distance
                            
                            candidates.append({
                                'allocation': alloc,
                                'shares_to_add': possible_additional_shares,
                                'additional_value': possible_additional_shares * alloc['price'],
                                'current_distance': distance_from_target,
                                'new_distance': new_distance,
                                'improvement_score': improvement_score,
                                'new_percent': new_percent
                            })
            
            if not candidates:
                print(f"   [SUCCESS] No more beneficial adjustments possible")
                break
            
            # Sort by improvement score (highest improvement first)
            candidates.sort(key=lambda x: x['improvement_score'], reverse=True)
            
            # Apply the best improvement
            best_candidate = candidates[0]
            allocation = best_candidate['allocation']
            shares_to_add = best_candidate['shares_to_add']
            additional_value = best_candidate['additional_value']
            
            # Update allocation
            allocation['shares'] += shares_to_add
            allocation['value'] += additional_value
            allocation['allocation_percent'] = (allocation['value'] / total_investment) * 100
            
            remaining_cash -= additional_value
            
            print(f"   [SUCCESS] Added {shares_to_add} shares to {allocation['symbol']} (LIVE price)")
            print(f"      {best_candidate['current_distance']:.2f}% to {best_candidate['new_distance']:.2f}% distance from target")
            print(f"      New allocation: {allocation['allocation_percent']:.2f}%")
            
            # If we made a very small improvement, try to make bigger moves
            if best_candidate['improvement_score'] < 0.1:  # Very small improvement
                # Look for opportunities to add multiple shares at once
                for candidate in candidates[:3]:  # Try top 3 candidates
                    alloc = candidate['allocation']
                    if remaining_cash >= alloc['price'] * 2:  # Can afford at least 2 more shares
                        max_additional = min(
                            math.floor(remaining_cash / alloc['price']),
                            candidate['shares_to_add']
                        )
                        if max_additional > 1:
                            additional_value = max_additional * alloc['price']
                            alloc['shares'] += max_additional
                            alloc['value'] += additional_value
                            alloc['allocation_percent'] = (alloc['value'] / total_investment) * 100
                            remaining_cash -= additional_value
                            print(f"   [INFO] Bulk added {max_additional} shares to {alloc['symbol']} (LIVE price)")
                            break
        
        print(f"   [SUCCESS] Optimization complete after {iteration} iterations")
        return remaining_cash
    
    def _calculate_allocation_stats(self, allocations: List[Dict]) -> Dict:
        """Calculate allocation statistics"""
        allocation_percents = [alloc['allocation_percent'] for alloc in allocations]
        
        # Calculate how many stocks are close to their individual targets (within 0.75%)
        close_to_target = 0
        for alloc in allocations:
            current_percent = alloc['allocation_percent']
            target_percent = alloc.get('target_allocation_percent', 5.0)
            if abs(current_percent - target_percent) <= 0.75:
                close_to_target += 1
        
        avg_target = sum(alloc.get('target_allocation_percent', 5.0) for alloc in allocations) / len(allocations)
        
        return {
            'min_allocation': min(allocation_percents),
            'max_allocation': max(allocation_percents),
            'avg_allocation': sum(allocation_percents) / len(allocation_percents),
            'std_deviation': self._calculate_std_dev(allocation_percents),
            'avg_target_allocation': avg_target,
            'close_to_target_count': close_to_target,
            'close_to_target_percentage': (close_to_target / len(allocation_percents)) * 100
        }
    
    def _validate_allocations(self, allocations: List[Dict], total_investment: float) -> Dict:
        """Validate that all allocations are within constraints"""
        validation_results = {
            'stocks_in_range': 0,
            'stocks_below_min': 0,
            'stocks_above_max': 0,
            'violations': []
        }
        
        for alloc in allocations:
            percent = alloc['allocation_percent']
            target_percent = alloc.get('target_allocation_percent', 5.0)
            
            # Dynamic min/max based on individual stock target
            min_allowed = target_percent - self.allocation_flexibility_percent
            max_allowed = target_percent + self.allocation_flexibility_percent
            
            if min_allowed <= percent <= max_allowed:
                validation_results['stocks_in_range'] += 1
            elif percent < min_allowed:
                validation_results['stocks_below_min'] += 1
                validation_results['violations'].append(
                    f"{alloc['symbol']}: {percent:.2f}% (below {min_allowed:.1f}% - target {target_percent:.1f}% ±{self.allocation_flexibility_percent}%)"
                )
            elif percent > max_allowed:
                validation_results['stocks_above_max'] += 1
                validation_results['violations'].append(
                    f"{alloc['symbol']}: {percent:.2f}% (above {max_allowed:.1f}% - target {target_percent:.1f}% ±{self.allocation_flexibility_percent}%)"
                )
        
        validation_results['all_valid'] = len(validation_results['violations']) == 0
        validation_results['success_rate'] = (validation_results['stocks_in_range'] / len(allocations)) * 100
        
        return validation_results
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)