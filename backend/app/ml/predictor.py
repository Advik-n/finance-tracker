"""
Spending Predictor

ML-based spending forecasting and predictions.
"""

from typing import List
from decimal import Decimal
from datetime import datetime, timedelta

from app.schemas.analytics import ForecastDataPoint


class SpendingPredictor:
    """
    Predictor for future spending patterns.
    
    Uses historical data to forecast future expenses
    with confidence intervals.
    """
    
    def __init__(self):
        self._model = None  # Would load actual ML model
    
    def forecast(
        self,
        historical_data: List[Decimal],
        months_ahead: int = 3,
    ) -> List[ForecastDataPoint]:
        """
        Forecast spending for future months.
        
        Args:
            historical_data: List of monthly spending amounts
            months_ahead: Number of months to forecast
            
        Returns:
            List of forecast data points
        """
        forecasts = []
        now = datetime.utcnow()
        
        if not historical_data:
            # No data - return zero forecasts
            for i in range(months_ahead):
                future_date = now + timedelta(days=(i + 1) * 30)
                forecasts.append(ForecastDataPoint(
                    month=future_date.strftime("%Y-%m"),
                    predicted_expenses=Decimal("0"),
                    confidence_lower=Decimal("0"),
                    confidence_upper=Decimal("0"),
                ))
            return forecasts
        
        # Simple forecasting using moving average
        # In production, would use proper ML models (Prophet, ARIMA, etc.)
        
        data = [float(d) for d in historical_data]
        
        # Calculate moving average
        window_size = min(3, len(data))
        recent_avg = sum(data[-window_size:]) / window_size
        
        # Calculate trend
        if len(data) >= 2:
            trend = (data[-1] - data[0]) / len(data)
        else:
            trend = 0
        
        # Calculate volatility for confidence intervals
        if len(data) >= 2:
            mean = sum(data) / len(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std_dev = variance ** 0.5
        else:
            std_dev = recent_avg * 0.2  # Assume 20% volatility
        
        # Generate forecasts
        for i in range(months_ahead):
            future_date = now + timedelta(days=(i + 1) * 30)
            
            # Predicted value with trend
            predicted = recent_avg + (trend * (i + 1))
            predicted = max(0, predicted)  # Can't have negative spending
            
            # Confidence intervals (widen over time)
            uncertainty = std_dev * (1 + i * 0.1)
            lower = max(0, predicted - 1.96 * uncertainty)
            upper = predicted + 1.96 * uncertainty
            
            forecasts.append(ForecastDataPoint(
                month=future_date.strftime("%Y-%m"),
                predicted_expenses=Decimal(str(round(predicted, 2))),
                confidence_lower=Decimal(str(round(lower, 2))),
                confidence_upper=Decimal(str(round(upper, 2))),
            ))
        
        return forecasts
    
    def detect_anomalies(
        self,
        historical_data: List[Decimal],
        current_spending: Decimal,
    ) -> bool:
        """
        Detect if current spending is anomalous.
        
        Args:
            historical_data: Historical spending data
            current_spending: Current period spending
            
        Returns:
            True if anomalous
        """
        if not historical_data:
            return False
        
        data = [float(d) for d in historical_data]
        current = float(current_spending)
        
        mean = sum(data) / len(data)
        
        if len(data) >= 2:
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std_dev = variance ** 0.5
        else:
            std_dev = mean * 0.3
        
        # Anomaly if more than 2 standard deviations from mean
        z_score = abs(current - mean) / std_dev if std_dev > 0 else 0
        
        return z_score > 2.0
    
    def calculate_seasonal_factors(
        self,
        historical_data: List[tuple],  # List of (month, amount)
    ) -> dict:
        """
        Calculate seasonal adjustment factors.
        
        Args:
            historical_data: List of (month, amount) tuples
            
        Returns:
            Dict of month -> seasonal factor
        """
        if not historical_data:
            return {i: 1.0 for i in range(1, 13)}
        
        # Group by month
        monthly_totals = {}
        monthly_counts = {}
        
        for month, amount in historical_data:
            if month not in monthly_totals:
                monthly_totals[month] = 0
                monthly_counts[month] = 0
            monthly_totals[month] += float(amount)
            monthly_counts[month] += 1
        
        # Calculate monthly averages
        monthly_avgs = {
            m: monthly_totals[m] / monthly_counts[m]
            for m in monthly_totals
        }
        
        # Calculate overall average
        overall_avg = sum(monthly_avgs.values()) / len(monthly_avgs)
        
        if overall_avg == 0:
            return {i: 1.0 for i in range(1, 13)}
        
        # Calculate seasonal factors
        factors = {}
        for month in range(1, 13):
            if month in monthly_avgs:
                factors[month] = monthly_avgs[month] / overall_avg
            else:
                factors[month] = 1.0
        
        return factors
