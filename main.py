#!/usr/bin/env python3
"""
한국투자증권 OpenAPI 주식 자동매매 프로그램
Main CLI Interface
"""
import argparse
import sys
from typing import Optional

from src.factory import KISClient
from src.infrastructure.config import Config
from src.backtest.engine import BacktestEngine
from src.backtest.data_provider import HistoricalDataProvider, MockHistoricalDataProvider, generate_sample_data
from src.backtest.models import BacktestResult


def print_price(client: KISClient, stock_code: str):
    """현재가 조회"""
    price = client.stock.get_price(stock_code)
    if price:
        print(f"\n=== {stock_code} 현재가 ===")
        for key, value in price.to_dict().items():
            if isinstance(value, int) and value >= 1000:
                print(f"  {key}: {value:,}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"시세 조회 실패: {stock_code}")


def print_asking_price(client: KISClient, stock_code: str):
    """호가 조회"""
    asking = client.stock.get_asking_price(stock_code)
    if asking:
        print(f"\n=== {stock_code} 호가 ===")
        for key, value in asking.to_dict().items():
            print(f"  {key}: {value:,}")
    else:
        print(f"호가 조회 실패: {stock_code}")


def print_daily_prices(client: KISClient, stock_code: str, count: int = 5):
    """일별 시세 조회"""
    prices = client.stock.get_daily_prices(stock_code)
    if prices:
        print(f"\n=== {stock_code} 일별 시세 (최근 {count}일) ===")
        for daily in prices[:count]:
            print(f"  {daily.date}: 종가 {daily.close_price:,}원, 거래량 {daily.volume:,}")
    else:
        print(f"일별 시세 조회 실패: {stock_code}")


def print_balance(client: KISClient):
    """잔고 조회"""
    balance = client.account.get_balance()
    if balance:
        print("\n=== 계좌 잔고 ===")
        print("\n[보유종목]")
        if balance.holdings:
            for h in balance.holdings:
                print(f"  {h.stock_name}({h.stock_code}): {h.quantity}주, "
                      f"평가금액 {h.eval_amount:,}원, 수익률 {h.profit_rate}%")
        else:
            print("  보유종목 없음")

        print("\n[계좌요약]")
        summary = balance.summary
        print(f"  예수금: {summary.deposit:,}원")
        print(f"  총매입금액: {summary.total_buy_amount:,}원")
        print(f"  총평가금액: {summary.total_eval_amount:,}원")
        print(f"  총평가손익: {summary.total_profit_loss:,}원")
    else:
        print("잔고 조회 실패")


def print_deposit(client: KISClient):
    """주문가능금액 조회"""
    deposit = client.account.get_available_deposit()
    if deposit:
        print("\n=== 주문가능금액 ===")
        print(f"  주문가능현금: {deposit.available_cash:,}원")
        print(f"  주문가능총액: {deposit.available_total:,}원")
    else:
        print("주문가능금액 조회 실패")


def execute_buy(client: KISClient, stock_code: str, quantity: int, price: int):
    """매수 주문"""
    order_type = "지정가" if price > 0 else "시장가"
    print(f"\n=== 매수 주문 ===")
    print(f"  종목: {stock_code}")
    print(f"  수량: {quantity}주")
    print(f"  가격: {price:,}원 ({order_type})")

    result = client.order.buy(stock_code, quantity, price)
    if result.success:
        print(f"\n주문 성공!")
        print(f"  주문번호: {result.order_no}")
        print(f"  주문시각: {result.order_time}")
    else:
        print(f"\n주문 실패: {result.message}")


def execute_sell(client: KISClient, stock_code: str, quantity: int, price: int):
    """매도 주문"""
    order_type = "지정가" if price > 0 else "시장가"
    print(f"\n=== 매도 주문 ===")
    print(f"  종목: {stock_code}")
    print(f"  수량: {quantity}주")
    print(f"  가격: {price:,}원 ({order_type})")

    result = client.order.sell(stock_code, quantity, price)
    if result.success:
        print(f"\n주문 성공!")
        print(f"  주문번호: {result.order_no}")
        print(f"  주문시각: {result.order_time}")
    else:
        print(f"\n주문 실패: {result.message}")


def print_orders(client: KISClient, date: Optional[str] = None):
    """주문 내역 조회"""
    orders = client.order.get_orders(date)
    if orders is not None:
        print("\n=== 주문/체결 내역 ===")
        if orders:
            for o in orders:
                print(f"  [{o.order_no}] {o.stock_name}({o.stock_code}) "
                      f"{o.order_side} {o.order_qty}주 @{o.order_price:,}원 -> {o.status}")
        else:
            print("  주문 내역 없음")
    else:
        print("주문 내역 조회 실패")


def run_backtest(
    client: Optional[KISClient],
    stock_code: str,
    start_date: str,
    end_date: str,
    capital: int,
    strategy: str,
    buy_price: int = 0,
    sell_price: int = 0,
    k: float = 0.5,
    target_profit: float = 2.0,
    stop_loss: float = -2.0,
    use_mock: bool = False,
):
    """백테스트 실행"""
    print(f"\n=== 백테스트 시작 ===")
    print(f"  종목코드: {stock_code}")
    print(f"  기간: {start_date} ~ {end_date}")
    print(f"  초기자본: {capital:,}원")
    print(f"  전략: {strategy}")

    # 전략 파라미터 설정
    if strategy == "range_trading":
        strategy_params = {
            "buy_price": buy_price,
            "sell_price": sell_price,
        }
        print(f"  매수가: {buy_price:,}원")
        print(f"  매도가: {sell_price:,}원")
    else:  # volatility_breakout
        strategy_params = {
            "k": k,
            "target_profit_rate": target_profit,
            "stop_loss_rate": stop_loss,
            "sell_at_close": True,
        }
        print(f"  K값: {k}")
        print(f"  목표수익률: {target_profit}%")
        print(f"  손절률: {stop_loss}%")

    # 데이터 제공자 설정
    if use_mock:
        print("\n[Mock 데이터 사용]")
        sample_data = generate_sample_data(start_date, end_date, base_price=buy_price or 50000)
        data_provider = MockHistoricalDataProvider(sample_data)
    else:
        if client is None:
            print("실제 데이터를 사용하려면 API 인증이 필요합니다.")
            print("--mock 옵션을 사용하거나 API 키를 설정하세요.")
            return
        data_provider = HistoricalDataProvider(client.stock)

    # 백테스트 엔진 실행
    engine = BacktestEngine(data_provider)
    result = engine.run(
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital,
        strategy=strategy,
        strategy_params=strategy_params,
        stock_name=stock_code,
    )

    # 결과 출력
    print(result.get_summary())

    # 거래 내역 출력
    if result.trades:
        print("\n[거래 내역]")
        for i, trade in enumerate(result.trades, 1):
            trade_dict = trade.to_dict()
            print(f"  {i}. {trade_dict['일자']} | {trade_dict['구분']} | "
                  f"{trade_dict['가격']:,}원 x {trade_dict['수량']}주 | "
                  f"손익: {trade_dict['손익']:,}원 ({trade_dict['수익률']}) | "
                  f"{trade_dict['사유']}")
    else:
        print("\n[거래 없음]")

    return result


def create_parser() -> argparse.ArgumentParser:
    """CLI 파서 생성"""
    parser = argparse.ArgumentParser(
        description="한국투자증권 OpenAPI 주식 자동매매 프로그램",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # 시세 조회
    price_parser = subparsers.add_parser("price", help="현재가 조회")
    price_parser.add_argument("stock_code", help="종목코드")

    # 호가 조회
    asking_parser = subparsers.add_parser("asking", help="호가 조회")
    asking_parser.add_argument("stock_code", help="종목코드")

    # 일별 시세
    daily_parser = subparsers.add_parser("daily", help="일별 시세 조회")
    daily_parser.add_argument("stock_code", help="종목코드")
    daily_parser.add_argument("-n", "--count", type=int, default=5, help="조회 일수")

    # 잔고 조회
    subparsers.add_parser("balance", help="계좌 잔고 조회")

    # 주문가능금액
    subparsers.add_parser("deposit", help="주문가능금액 조회")

    # 매수
    buy_parser = subparsers.add_parser("buy", help="매수 주문")
    buy_parser.add_argument("stock_code", help="종목코드")
    buy_parser.add_argument("quantity", type=int, help="수량")
    buy_parser.add_argument("price", type=int, help="가격 (0=시장가)")

    # 매도
    sell_parser = subparsers.add_parser("sell", help="매도 주문")
    sell_parser.add_argument("stock_code", help="종목코드")
    sell_parser.add_argument("quantity", type=int, help="수량")
    sell_parser.add_argument("price", type=int, help="가격 (0=시장가)")

    # 주문 내역
    orders_parser = subparsers.add_parser("orders", help="주문 내역 조회")
    orders_parser.add_argument("-d", "--date", help="조회일자 (YYYYMMDD)")

    # 백테스트
    backtest_parser = subparsers.add_parser("backtest", help="백테스트 시뮬레이션")
    backtest_parser.add_argument("stock_code", help="종목코드")
    backtest_parser.add_argument("start_date", help="시작일 (YYYYMMDD)")
    backtest_parser.add_argument("end_date", help="종료일 (YYYYMMDD)")
    backtest_parser.add_argument("-c", "--capital", type=int, default=1000000, help="초기 자본금 (기본: 1,000,000)")
    backtest_parser.add_argument(
        "-s", "--strategy",
        choices=["range_trading", "volatility_breakout"],
        default="range_trading",
        help="거래 전략 (기본: range_trading)"
    )
    backtest_parser.add_argument("--buy-price", type=int, default=0, help="[Range] 매수가")
    backtest_parser.add_argument("--sell-price", type=int, default=0, help="[Range] 매도가")
    backtest_parser.add_argument("--k", type=float, default=0.5, help="[VB] K값 (기본: 0.5)")
    backtest_parser.add_argument("--target-profit", type=float, default=2.0, help="[VB] 목표 수익률 %% (기본: 2.0)")
    backtest_parser.add_argument("--stop-loss", type=float, default=-2.0, help="[VB] 손절 수익률 %% (기본: -2.0)")
    backtest_parser.add_argument("--mock", action="store_true", help="Mock 데이터 사용 (API 미사용)")

    return parser


def main():
    """메인 함수"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # 백테스트는 --mock 옵션으로 API 없이 실행 가능
        if args.command == "backtest" and args.mock:
            run_backtest(
                client=None,
                stock_code=args.stock_code,
                start_date=args.start_date,
                end_date=args.end_date,
                capital=args.capital,
                strategy=args.strategy,
                buy_price=args.buy_price,
                sell_price=args.sell_price,
                k=args.k,
                target_profit=args.target_profit,
                stop_loss=args.stop_loss,
                use_mock=True,
            )
            return

        # 클라이언트 초기화
        client = KISClient()
        if not client.authenticate():
            print("인증 실패. API 키를 확인하세요.")
            sys.exit(1)
        print("인증 성공")

        # 명령어 실행
        if args.command == "price":
            print_price(client, args.stock_code)
        elif args.command == "asking":
            print_asking_price(client, args.stock_code)
        elif args.command == "daily":
            print_daily_prices(client, args.stock_code, args.count)
        elif args.command == "balance":
            print_balance(client)
        elif args.command == "deposit":
            print_deposit(client)
        elif args.command == "buy":
            execute_buy(client, args.stock_code, args.quantity, args.price)
        elif args.command == "sell":
            execute_sell(client, args.stock_code, args.quantity, args.price)
        elif args.command == "orders":
            print_orders(client, args.date)
        elif args.command == "backtest":
            run_backtest(
                client=client,
                stock_code=args.stock_code,
                start_date=args.start_date,
                end_date=args.end_date,
                capital=args.capital,
                strategy=args.strategy,
                buy_price=args.buy_price,
                sell_price=args.sell_price,
                k=args.k,
                target_profit=args.target_profit,
                stop_loss=args.stop_loss,
                use_mock=False,
            )

    except ValueError as e:
        print(f"설정 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
