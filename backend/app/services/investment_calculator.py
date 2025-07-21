# backend/app/services/investment_calculator.py
from typing import Dict, List, Tuple
import math

class InvestmentCalculator:
    def __init__(self):
        self.min_allocation_percent = 4.0  # 4%
        self.target_allocation_percent = 5.0  # 5%
        self.max_allocation_percent = 7.0  # 7%
    
    def calculate_minimum_investment(self, stocks_data: List[Dict]) -> Dict:
        """
        Calculate minimum investment required for 4% allocation per stock
        """
        try:
            print(f"🧮 Calculating minimum investment for {len(stocks_data)} stocks...")
            
            if not stocks_data:
                raise Exception("No stocks data provided")
            
            # Find the most expensive stock for 4% allocation
            min_investments = []
            stock_details = []
            
            for stock in stocks_data:
                symbol = stock.get('symbol')
                price = stock.get('price')
                
                if not symbol or not price or price <= 0:
                    print(f"   ⚠️ Skipping {symbol}: Invalid price ({price})")
                    continue
                
                # For 4% allocation, we need at least 1 share
                # So minimum investment = price / 0.04 = price * 25
                min_investment_for_stock = price * (100 / self.min_allocation_percent)
                min_shares_needed = 1
                
                min_investments.append(min_investment_for_stock)
                stock_details.append({
                    'symbol': symbol,
                    'price': price,
                    'min_investment_for_4pct': min_investment_for_stock,
                    'min_shares': min_shares_needed
                })
                
                print(f"   {symbol}: ₹{price:.2f}/share → Min investment: ₹{min_investment_for_stock:,.0f}")
            
            if not min_investments:
                raise Exception("No valid stocks with prices found")
            
            # The minimum investment is the maximum of all individual minimums
            total_minimum_investment = max(min_investments)
            
            # Add a buffer to ensure we can get closer to 5% for all stocks
            buffer_percent = 20  # 20% buffer
            recommended_minimum = total_minimum_investment * (1 + buffer_percent / 100)
            
            result = {
                'minimum_investment': total_minimum_investment,
                'recommended_minimum': recommended_minimum,
                'buffer_percent': buffer_percent,
                'total_stocks': len(stock_details),
                'valid_stocks': len(stock_details),
                'invalid_stocks': len(stocks_data) - len(stock_details),
                'stock_details': stock_details,
                'most_expensive_stock': max(stock_details, key=lambda x: x['price']) if stock_details else None,
                'calculation_basis': f"Based on {self.min_allocation_percent}% minimum allocation per stock"
            }
            
            print(f"✅ Minimum investment calculated:")
            print(f"   Valid stocks: {len(stock_details)}/{len(stocks_data)}")
            print(f"   Absolute minimum: ₹{total_minimum_investment:,.0f}")
            print(f"   Recommended minimum: ₹{recommended_minimum:,.0f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error calculating minimum investment: {e}")
            raise Exception(f"Failed to calculate minimum investment: {str(e)}")
    
    def calculate_optimal_allocation(self, investment_amount: float, stocks_data: List[Dict]) -> Dict:
        """
        Calculate optimal allocation using sophisticated algorithm
        Ensures each stock gets 4-7% allocation, as close to 5% as possible
        """
        try:
            print(f"🎯 Calculating optimal allocation for ₹{investment_amount:,.0f}")
            print(f"   Target: {self.min_allocation_percent}%-{self.max_allocation_percent}% per stock, close to {self.target_allocation_percent}%")
            
            # Phase 1: Initial allocation (target 5% each)
            target_per_stock = investment_amount * (self.target_allocation_percent / 100)
            allocations = []
            total_allocated = 0
            
            print(f"📊 Phase 1: Initial allocation (₹{target_per_stock:,.0f} per stock)")
            
            for stock in stocks_data:
                symbol = stock['symbol']
                price = stock['price']
                
                # Calculate constraints
                min_value = investment_amount * (self.min_allocation_percent / 100)
                max_value = investment_amount * (self.max_allocation_percent / 100)
                
                min_shares = max(1, math.ceil(min_value / price))  # At least 1 share
                max_shares = math.floor(max_value / price)
                
                # Target shares for 5% allocation
                target_shares = math.floor(target_per_stock / price)
                
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
                    'shares': optimal_shares,
                    'value': allocation_value,
                    'allocation_percent': allocation_percent,
                    'min_shares': min_shares,
                    'max_shares': max_shares,
                    'target_met': abs(allocation_percent - self.target_allocation_percent) < 0.5
                }
                
                allocations.append(allocation)
                total_allocated += allocation_value
                
                print(f"   {symbol}: {optimal_shares} shares × ₹{price:.2f} = ₹{allocation_value:,.0f} ({allocation_percent:.2f}%)")
            
            remaining_cash = investment_amount - total_allocated
            print(f"📊 After initial allocation: ₹{remaining_cash:,.0f} remaining")
            
            # Phase 2: Distribute remaining cash optimally
            if remaining_cash > 0:
                print(f"💰 Phase 2: Distributing remaining ₹{remaining_cash:,.0f}")
                remaining_cash = self._distribute_remaining_cash(allocations, remaining_cash, investment_amount)
            
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
                'validation': self._validate_allocations(allocations, investment_amount)
            }
            
            print(f"✅ Optimal allocation calculated:")
            print(f"   Total allocated: ₹{final_total:,.0f} ({(final_total/investment_amount)*100:.2f}%)")
            print(f"   Remaining cash: ₹{final_remaining:,.0f}")
            print(f"   Stocks in range: {allocation_summary['validation']['stocks_in_range']}/{len(allocations)}")
            
            return allocation_summary
            
        except Exception as e:
            print(f"❌ Error calculating optimal allocation: {e}")
            raise Exception(f"Failed to calculate optimal allocation: {str(e)}")
    
    def _distribute_remaining_cash(self, allocations: List[Dict], remaining_cash: float, total_investment: float) -> float:
        """Distribute remaining cash to stocks that can accept more allocation"""
        
        iteration = 0
        max_iterations = 10
        
        while remaining_cash > 100 and iteration < max_iterations:  # Stop if less than ₹100 or max iterations
            iteration += 1
            print(f"   Iteration {iteration}: ₹{remaining_cash:,.0f} to distribute")
            
            # Find stocks that can accept more allocation (under 7% limit)
            candidates = []
            for alloc in allocations:
                current_percent = (alloc['value'] / total_investment) * 100
                max_additional_value = (total_investment * (self.max_allocation_percent / 100)) - alloc['value']
                
                if max_additional_value > alloc['price']:  # Can buy at least 1 more share
                    max_additional_shares = math.floor(max_additional_value / alloc['price'])
                    candidates.append({
                        'allocation': alloc,
                        'max_additional_shares': max_additional_shares,
                        'max_additional_value': max_additional_shares * alloc['price'],
                        'distance_from_target': abs(current_percent - self.target_allocation_percent)
                    })
            
            if not candidates:
                print(f"   No candidates found for additional allocation")
                break
            
            # Sort by distance from target (prioritize stocks furthest from 5%)
            candidates.sort(key=lambda x: x['distance_from_target'], reverse=True)
            
            distributed_in_iteration = 0
            for candidate in candidates:
                if remaining_cash < candidate['allocation']['price']:
                    continue
                
                # Calculate how many shares we can add
                affordable_shares = math.floor(remaining_cash / candidate['allocation']['price'])
                shares_to_add = min(affordable_shares, candidate['max_additional_shares'])
                
                if shares_to_add > 0:
                    additional_value = shares_to_add * candidate['allocation']['price']
                    
                    # Update allocation
                    candidate['allocation']['shares'] += shares_to_add
                    candidate['allocation']['value'] += additional_value
                    candidate['allocation']['allocation_percent'] = (candidate['allocation']['value'] / total_investment) * 100
                    
                    remaining_cash -= additional_value
                    distributed_in_iteration += additional_value
                    
                    print(f"   Added {shares_to_add} shares to {candidate['allocation']['symbol']} → {candidate['allocation']['allocation_percent']:.2f}%")
            
            if distributed_in_iteration == 0:
                print(f"   No more distribution possible")
                break
        
        return remaining_cash
    
    def _calculate_allocation_stats(self, allocations: List[Dict]) -> Dict:
        """Calculate allocation statistics"""
        allocation_percents = [alloc['allocation_percent'] for alloc in allocations]
        
        return {
            'min_allocation': min(allocation_percents),
            'max_allocation': max(allocation_percents),
            'avg_allocation': sum(allocation_percents) / len(allocation_percents),
            'std_deviation': self._calculate_std_dev(allocation_percents),
            'target_allocation': self.target_allocation_percent
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
                validation_results['violations'].append(f"{alloc['symbol']}: {percent:.2f}% (below {self.min_allocation_percent}%)")
            elif percent > self.max_allocation_percent:
                validation_results['stocks_above_max'] += 1
                validation_results['violations'].append(f"{alloc['symbol']}: {percent:.2f}% (above {self.max_allocation_percent}%)")
        
        validation_results['all_valid'] = len(validation_results['violations']) == 0
        
        return validation_results
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)