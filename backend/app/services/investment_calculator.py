# backend/app/services/investment_calculator.py
from typing import Dict, List, Tuple
import math

class InvestmentCalculator:
    def __init__(self):
        self.min_allocation_percent = 3.5  # 5% - 1.5% = 3.5%
        self.target_allocation_percent = 5.0  # 5%
        self.max_allocation_percent = 6.5  # 5% + 1.5% = 6.5%
    
    def calculate_minimum_investment(self, stocks_data: List[Dict]) -> Dict:
        """
        Calculate minimum investment required for 4% allocation per stock
        STRICT: Only works with REAL price data
        """
        try:
            print(f"[INFO] Calculating minimum investment for {len(stocks_data)} stocks...")
            
            if not stocks_data:
                raise Exception("No stocks data provided")
            
            # STRICT: Verify all stocks have real prices
            invalid_stocks = []
            for stock in stocks_data:
                price = stock.get('price', 0)
                price_type = stock.get('price_type', 'UNKNOWN')
                
                if price_type != 'LIVE':
                    invalid_stocks.append(f"{stock.get('symbol', 'UNKNOWN')}: {price_type}")
                elif not isinstance(price, (int, float)) or price <= 0:
                    invalid_stocks.append(f"{stock.get('symbol', 'UNKNOWN')}: Invalid price {price}")
            
            if invalid_stocks:
                raise Exception(f"PRICE_DATA_INVALID: Found {len(invalid_stocks)} stocks without valid live prices: {', '.join(invalid_stocks[:5])}")
            
            # Find the most expensive stock
            most_expensive_stock = max(stocks_data, key=lambda x: x['price'])
            max_price = most_expensive_stock['price']
            
            print(f"   Most expensive stock: {most_expensive_stock['symbol']} at Rs.{max_price:,.2f} (LIVE)")
            
            # For the most expensive stock to have 3.5% allocation with at least 1 share:
            # min_investment = price / 0.035 = price * 28.57
            min_investment_required = max_price * (100 / self.min_allocation_percent)
            
            # Add buffer to ensure all stocks can get close to 5% allocation
            buffer_percent = 20  # 20% buffer
            recommended_minimum = min_investment_required * (1 + buffer_percent / 100)
            
            # Calculate details for each stock
            stock_details = []
            for stock in stocks_data:
                symbol = stock['symbol']
                price = stock['price']
                
                min_investment_for_stock = price * (100 / self.min_allocation_percent)
                
                stock_details.append({
                    'symbol': symbol,
                    'price': price,
                    'price_type': 'LIVE',
                    'min_investment_for_3_5pct': min_investment_for_stock,
                    'min_shares': 1
                })
                
                print(f"   {symbol}: Rs.{price:.2f}/share (LIVE) - Min investment for 3.5%: Rs.{min_investment_for_stock:,.0f}")
            
            result = {
                'minimum_investment': min_investment_required,
                'recommended_minimum': recommended_minimum,
                'buffer_percent': buffer_percent,
                'total_stocks': len(stock_details),
                'valid_stocks': len(stock_details),
                'invalid_stocks': 0,
                'stock_details': stock_details,
                'most_expensive_stock': most_expensive_stock,
                'calculation_basis': f"Based on most expensive stock ({most_expensive_stock['symbol']}) having {self.min_allocation_percent}% allocation (5% ±1.5% range)",
                'data_quality': 'HIGH - All prices from live API'
            }
            
            print(f"[SUCCESS] Minimum investment calculated with LIVE data:")
            print(f"   Absolute minimum: Rs.{min_investment_required:,.0f}")
            print(f"   Recommended minimum: Rs.{recommended_minimum:,.0f}")
            print(f"   Data quality: HIGH - All live prices")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error calculating minimum investment: {e}")
            raise Exception(f"Failed to calculate minimum investment: {str(e)}")
    
    def calculate_optimal_allocation(self, investment_amount: float, stocks_data: List[Dict]) -> Dict:
        """
        Calculate optimal allocation using sophisticated algorithm
        STRICT: Only works with REAL price data
        """
        try:
            print(f"[INFO] Calculating optimal allocation for Rs.{investment_amount:,.0f}")
            print(f"   Target: {self.min_allocation_percent}%-{self.max_allocation_percent}% per stock (5% ±1.5%), ideally {self.target_allocation_percent}%")
            
            # STRICT: Verify all stocks have real prices
            invalid_stocks = []
            for stock in stocks_data:
                price = stock.get('price', 0)
                price_type = stock.get('price_type', 'UNKNOWN')
                
                if price_type != 'LIVE':
                    invalid_stocks.append(f"{stock.get('symbol', 'UNKNOWN')}: {price_type}")
                elif not isinstance(price, (int, float)) or price <= 0:
                    invalid_stocks.append(f"{stock.get('symbol', 'UNKNOWN')}: Invalid price {price}")
            
            if invalid_stocks:
                raise Exception(f"PRICE_DATA_INVALID: Found {len(invalid_stocks)} stocks without valid live prices: {', '.join(invalid_stocks[:5])}")
            
            # Phase 1: Initial allocation targeting 5% each
            target_per_stock = investment_amount * (self.target_allocation_percent / 100)
            allocations = []
            total_allocated = 0
            
            print(f"[INFO] Phase 1: Initial allocation (Rs.{target_per_stock:,.0f} per stock) - ALL LIVE PRICES")
            
            for stock in stocks_data:
                symbol = stock['symbol']
                price = stock['price']
                
                # Calculate constraints
                min_value = investment_amount * (self.min_allocation_percent / 100)
                max_value = investment_amount * (self.max_allocation_percent / 100)
                
                min_shares = max(1, math.ceil(min_value / price))  # At least 1 share
                max_shares = math.floor(max_value / price)
                
                # Start with target shares for 5% allocation
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
                    'min_shares': min_shares,
                    'max_shares': max_shares,
                    'target_met': abs(allocation_percent - self.target_allocation_percent) < 0.5
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
            
        except Exception as e:
            print(f"[ERROR] Error calculating optimal allocation: {e}")
            raise Exception(f"Failed to calculate optimal allocation: {str(e)}")
    
    def _optimize_allocation(self, allocations: List[Dict], remaining_cash: float, total_investment: float) -> float:
        """
        Sophisticated optimization to distribute remaining cash
        Prioritizes getting stocks closer to 5% target
        """
        
        iteration = 0
        max_iterations = 20  # Increased iterations for better optimization
        min_improvement = 100  # Stop if improvement is less than Rs.100
        
        while remaining_cash > min_improvement and iteration < max_iterations:
            iteration += 1
            print(f"   [INFO] Optimization iteration {iteration}: Rs.{remaining_cash:,.0f} to distribute")
            
            # Calculate how far each stock is from 5% target
            candidates = []
            for alloc in allocations:
                current_percent = (alloc['value'] / total_investment) * 100
                distance_from_target = abs(current_percent - self.target_allocation_percent)
                
                # Check if we can add shares without exceeding 7% limit
                max_additional_value = (total_investment * (self.max_allocation_percent / 100)) - alloc['value']
                
                if max_additional_value > alloc['price']:  # Can buy at least 1 more share
                    max_additional_shares = math.floor(max_additional_value / alloc['price'])
                    affordable_shares = math.floor(remaining_cash / alloc['price'])
                    possible_additional_shares = min(max_additional_shares, affordable_shares)
                    
                    if possible_additional_shares > 0:
                        # Calculate what the new allocation would be
                        new_value = alloc['value'] + (possible_additional_shares * alloc['price'])
                        new_percent = (new_value / total_investment) * 100
                        new_distance = abs(new_percent - self.target_allocation_percent)
                        
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
        
        # Calculate how many stocks are close to target (within 0.5%)
        close_to_target = sum(1 for pct in allocation_percents 
                             if abs(pct - self.target_allocation_percent) <= 0.75)  # Within ±0.75% is considered close
        
        return {
            'min_allocation': min(allocation_percents),
            'max_allocation': max(allocation_percents),
            'avg_allocation': sum(allocation_percents) / len(allocation_percents),
            'std_deviation': self._calculate_std_dev(allocation_percents),
            'target_allocation': self.target_allocation_percent,
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
            
            if self.min_allocation_percent <= percent <= self.max_allocation_percent:
                validation_results['stocks_in_range'] += 1
            elif percent < self.min_allocation_percent:
                validation_results['stocks_below_min'] += 1
                validation_results['violations'].append(
                    f"{alloc['symbol']}: {percent:.2f}% (below {self.min_allocation_percent}% - outside 5% ±1.5% range)"
                )
            elif percent > self.max_allocation_percent:
                validation_results['stocks_above_max'] += 1
                validation_results['violations'].append(
                    f"{alloc['symbol']}: {percent:.2f}% (above {self.max_allocation_percent}% - outside 5% ±1.5% range)"
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