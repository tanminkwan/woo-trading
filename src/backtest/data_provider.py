"""
Historical Data Provider - 과거 데이터 제공자 구현 (DIP 준수)
"""
from typing import List, Optional
from datetime import datetime, timedelta

from ..domain.interfaces import IHistoricalDataProvider, IStockService
from ..domain.models import DailyPrice, MinutePrice


class HistoricalDataProvider(IHistoricalDataProvider):
    """과거 시세 데이터 제공자

    IStockService를 주입받아 실제 API로부터 데이터를 조회합니다.
    """

    def __init__(self, stock_service: IStockService):
        self._stock_service = stock_service

    def get_daily_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> List[DailyPrice]:
        """일별 시세 데이터 조회

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            일별 시세 리스트 (날짜 오름차순)
        """
        # API로부터 일별 시세 조회
        daily_prices = self._stock_service.get_daily_prices(stock_code)

        if not daily_prices:
            return []

        # 기간 필터링
        filtered = [
            dp for dp in daily_prices
            if start_date <= dp.date <= end_date
        ]

        # 날짜 오름차순 정렬
        filtered.sort(key=lambda x: x.date)

        return filtered

    def get_minute_data(
        self,
        stock_code: str,
        date: str,
    ) -> List[MinutePrice]:
        """분봉 시세 데이터 조회

        Args:
            stock_code: 종목코드
            date: 조회일 (YYYYMMDD)

        Returns:
            분봉 시세 리스트 (시간 오름차순)
        """
        minute_prices = self._stock_service.get_minute_prices(stock_code)

        if not minute_prices:
            return []

        # 해당 날짜만 필터링
        filtered = [mp for mp in minute_prices if mp.date == date]

        # 시간 오름차순 정렬
        filtered.sort(key=lambda x: x.datetime)

        return filtered


class MockHistoricalDataProvider(IHistoricalDataProvider):
    """테스트용 Mock 데이터 제공자

    주어진 데이터를 그대로 반환합니다. 테스트 시 사용.
    """

    def __init__(
        self,
        daily_data: Optional[List[DailyPrice]] = None,
        minute_data: Optional[List[MinutePrice]] = None,
    ):
        self._daily_data = daily_data or []
        self._minute_data = minute_data or []

    def set_daily_data(self, data: List[DailyPrice]):
        """일별 테스트 데이터 설정"""
        self._daily_data = data

    def set_minute_data(self, data: List[MinutePrice]):
        """분봉 테스트 데이터 설정"""
        self._minute_data = data

    def get_daily_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> List[DailyPrice]:
        """설정된 일별 데이터 반환 (기간 필터링 적용)"""
        filtered = [
            dp for dp in self._daily_data
            if start_date <= dp.date <= end_date
        ]
        filtered.sort(key=lambda x: x.date)
        return filtered

    def get_minute_data(
        self,
        stock_code: str,
        date: str,
    ) -> List[MinutePrice]:
        """설정된 분봉 데이터 반환 (날짜 필터링 적용)"""
        filtered = [mp for mp in self._minute_data if mp.date == date]
        filtered.sort(key=lambda x: x.datetime)
        return filtered


def generate_sample_data(
    start_date: str,
    end_date: str,
    base_price: int = 50000,
    volatility: float = 0.02,
) -> List[DailyPrice]:
    """테스트용 샘플 데이터 생성

    Args:
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)
        base_price: 기준 가격
        volatility: 변동성 (비율)

    Returns:
        샘플 일별 시세 리스트
    """
    import random

    result = []
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    current_price = base_price

    while current_date <= end:
        # 주말 제외
        if current_date.weekday() < 5:
            # 일일 변동 계산
            change = random.uniform(-volatility, volatility)
            open_price = int(current_price * (1 + random.uniform(-0.005, 0.005)))
            high_price = int(max(open_price, current_price) * (1 + random.uniform(0, volatility)))
            low_price = int(min(open_price, current_price) * (1 - random.uniform(0, volatility)))
            close_price = int(current_price * (1 + change))

            # 가격 일관성 보장
            high_price = max(open_price, close_price, high_price)
            low_price = min(open_price, close_price, low_price)

            result.append(
                DailyPrice(
                    date=current_date.strftime("%Y%m%d"),
                    close_price=close_price,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    volume=random.randint(1000000, 10000000),
                )
            )
            current_price = close_price

        current_date += timedelta(days=1)

    return result


def generate_minute_sample_data(
    start_date: str,
    end_date: str,
    base_price: int = 50000,
    volatility: float = 0.005,
) -> List[MinutePrice]:
    """테스트용 분봉 샘플 데이터 생성

    Args:
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)
        base_price: 기준 가격
        volatility: 변동성 (비율) - 분봉은 일봉보다 작은 변동성

    Returns:
        샘플 분봉 시세 리스트
    """
    import random

    result = []
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    current_price = base_price

    # 장 시간: 09:00 ~ 15:30
    market_open_hour = 9
    market_open_minute = 0
    market_close_hour = 15
    market_close_minute = 30

    while current_date <= end:
        # 주말 제외
        if current_date.weekday() < 5:
            # 장 시작 가격 (전일 종가 기준 약간의 갭)
            day_open_price = int(current_price * (1 + random.uniform(-0.01, 0.01)))
            current_price = day_open_price

            # 분봉 생성 (1분 간격)
            current_time = current_date.replace(hour=market_open_hour, minute=market_open_minute)
            market_close = current_date.replace(hour=market_close_hour, minute=market_close_minute)

            while current_time <= market_close:
                # 분당 변동 계산
                change = random.uniform(-volatility, volatility)
                open_price = current_price
                close_price = int(current_price * (1 + change))
                high_price = int(max(open_price, close_price) * (1 + random.uniform(0, volatility / 2)))
                low_price = int(min(open_price, close_price) * (1 - random.uniform(0, volatility / 2)))

                # 가격 일관성 보장
                high_price = max(open_price, close_price, high_price)
                low_price = min(open_price, close_price, low_price)

                datetime_str = current_time.strftime("%Y%m%d%H%M%S")

                result.append(
                    MinutePrice(
                        datetime=datetime_str,
                        close_price=close_price,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        volume=random.randint(1000, 50000),
                    )
                )
                current_price = close_price
                current_time += timedelta(minutes=1)

        current_date += timedelta(days=1)

    return result
