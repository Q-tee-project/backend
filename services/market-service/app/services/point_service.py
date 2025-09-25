from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from ..models.market import UserPoint, PointTransaction, PointTransactionType
from ..schemas.market import UserPointResponse, PointTransactionResponse


class PointService:
    """포인트 시스템 서비스"""

    @staticmethod
    async def get_user_points(db: Session, user_id: int) -> UserPointResponse:
        """사용자 포인트 정보 조회"""
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()

        if not user_point:
            # 포인트 계정이 없으면 생성 (0포인트로 시작)
            user_point = UserPoint(
                user_id=user_id,
                available_points=0,
                total_earned=0,
                total_spent=0,
                total_charged=0
            )
            db.add(user_point)
            db.commit()
            db.refresh(user_point)

        return UserPointResponse.from_orm(user_point)

    @staticmethod
    async def charge_points(db: Session, user_id: int, amount: int) -> PointTransactionResponse:
        """포인트 충전"""
        if amount <= 0:
            raise ValueError("충전 금액은 0보다 커야 합니다.")

        if amount % 1000 != 0:
            raise ValueError("1,000 포인트 단위로만 충전 가능합니다.")

        # 사용자 포인트 계정 조회 또는 생성
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()
        if not user_point:
            user_point = UserPoint(
                user_id=user_id,
                available_points=0,
                total_earned=0,
                total_spent=0,
                total_charged=0
            )
            db.add(user_point)

        # 포인트 충전
        user_point.available_points += amount
        user_point.total_charged += amount

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=PointTransactionType.CHARGE,
            amount=amount,
            balance_after=user_point.available_points,
            description=f"{amount:,} 포인트 충전"
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return PointTransactionResponse.from_orm(transaction)

    @staticmethod
    async def spend_points(db: Session, user_id: int, amount: int,
                          product_id: int, description: str) -> PointTransactionResponse:
        """포인트 사용 (구매)"""
        if amount <= 0:
            raise ValueError("사용 금액은 0보다 커야 합니다.")

        # 사용자 포인트 확인
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()
        if not user_point or user_point.available_points < amount:
            raise ValueError(f"포인트가 부족합니다. (보유: {user_point.available_points if user_point else 0}, 필요: {amount})")

        # 포인트 차감
        user_point.available_points -= amount
        user_point.total_spent += amount

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=PointTransactionType.PURCHASE,
            amount=-amount,  # 음수로 저장 (차감)
            balance_after=user_point.available_points,
            product_id=product_id,
            description=description
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return PointTransactionResponse.from_orm(transaction)

    @staticmethod
    async def earn_points(db: Session, user_id: int, amount: int,
                         product_id: int, description: str) -> PointTransactionResponse:
        """포인트 획득 (판매 수익)"""
        if amount <= 0:
            raise ValueError("수익 금액은 0보다 커야 합니다.")

        # 사용자 포인트 계정 조회 또는 생성
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()
        if not user_point:
            user_point = UserPoint(
                user_id=user_id,
                available_points=0,
                total_earned=0,
                total_spent=0,
                total_charged=0
            )
            db.add(user_point)

        # 포인트 적립
        user_point.available_points += amount
        user_point.total_earned += amount

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=PointTransactionType.EARN,
            amount=amount,
            balance_after=user_point.available_points,
            product_id=product_id,
            description=description
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return PointTransactionResponse.from_orm(transaction)

    @staticmethod
    async def get_user_transactions(db: Session, user_id: int,
                                   skip: int = 0, limit: int = 20) -> List[PointTransactionResponse]:
        """사용자 포인트 거래 내역"""
        transactions = (
            db.query(PointTransaction)
            .filter(PointTransaction.user_id == user_id)
            .order_by(desc(PointTransaction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [PointTransactionResponse.from_orm(t) for t in transactions]

    @staticmethod
    async def get_balance(db: Session, user_id: int) -> int:
        """사용자 포인트 잔액 조회 (간단 버전)"""
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()
        return user_point.available_points if user_point else 0

    @staticmethod
    async def admin_adjust_points(db: Session, user_id: int, amount: int,
                                 reason: str) -> PointTransactionResponse:
        """관리자 포인트 조정"""
        user_point = db.query(UserPoint).filter(UserPoint.user_id == user_id).first()
        if not user_point:
            user_point = UserPoint(
                user_id=user_id,
                available_points=0,
                total_earned=0,
                total_spent=0,
                total_charged=0
            )
            db.add(user_point)

        # 음수 잔액 방지
        if user_point.available_points + amount < 0:
            raise ValueError("조정 후 잔액이 음수가 될 수 없습니다.")

        # 포인트 조정
        user_point.available_points += amount
        if amount > 0:
            user_point.total_charged += amount
        else:
            user_point.total_spent += abs(amount)

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=PointTransactionType.ADMIN_ADJUST,
            amount=amount,
            balance_after=user_point.available_points,
            description=f"관리자 조정: {reason}"
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return PointTransactionResponse.from_orm(transaction)