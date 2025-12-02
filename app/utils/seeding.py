import asyncio
import random
import string
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.roles import Role
from ..models.roles_permissions import RolePermission
from ..models.permissions import Permission 
from ..models.admins import Admin
from ..models.users import User, UserStatus, UserType
from ..models.users_archieve import UserArchieve
from ..models.user_preference import UserPreference
from ..models.plan_groups import PlanGroup
from ..models.plans import Plan, PlanStatus, PlanType
from ..models.offer_types import OfferType
from ..models.offers import Offer, OfferStatus
from ..models.autopay import AutoPay
from ..models.current_active_plans import CurrentActivePlan, CurrentPlanStatus
from ..models.backup import Backup
from ..models.transactions import Transaction, TransactionCategory, TransactionSource, TransactionStatus, TransactionType, ServiceType, PaymentMethod
from ..models.referral import ReferralReward, ReferralRewardStatus
from ..core.database import AsyncSessionLocal  


async def seed_permissions(session: AsyncSession):
    """
    Seed the `Permission` table if it's empty.

    This function inserts a predefined set of permissions. If the table already
    contains entries the function will do nothing.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB insert/flush fails.
    """
    existing = await session.execute(select(Permission))
    existing_permissions = existing.scalars().all()

    if existing_permissions:
        print("permissions already exist, skipping seeding.")
        return

    print("seeding permissions...")

    permissions_data = [
        {"permission_id": 1, "resource": "Users", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 2, "resource": "Posts", "read": True, "write": True, "delete": False, "edit": True},
        {"permission_id": 3, "resource": "Reports", "read": True, "write": False, "delete": False, "edit": False},
        {"permission_id": 4, "resource": "Admins", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 5, "resource": "Admin_me", "read": True, "write": False, "delete": True, "edit": True},
        {"permission_id": 6, "resource": "PlanGroups", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 8, "resource": "Plans", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 9, "resource": "OfferType", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 10, "resource": "Offers", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 11, "resource": "Recharge", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 12, "resource": "Autopay", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 13, "resource": "Referral", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 14, "resource": "Contact-form", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 15, "resource": "Content", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 16, "resource": "Announcement", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 17, "resource": "Backup", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 18, "resource": "Sessions", "read": True, "write": True, "delete": True, "edit": True},
        {"permission_id": 19, "resource": "Roles", "read": True, "write": True, "delete": True, "edit": True},
    ]

    session.add_all([Permission(**p) for p in permissions_data])
    await session.flush()
    print("permissions seeded successfully.")


async def seed_roles_and_role_permissions(session: AsyncSession):
    """
    Seed default roles and associated role-permission mappings.

    Inserts a small set of roles and creates `RolePermission` entries based on
    the available `Permission` records. If any roles already exist the function
    will skip seeding.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """

    existing_roles = await session.execute(select(Role))
    existing_roles = existing_roles.scalars().all()

    if existing_roles:
        print("Roles already exist, skipping seeding.")
        return

    print("seeding roles...")

    roles_data = [
        {"role_name": "SuperAdmin"},
        {"role_name": "Manager"},
        {"role_name": "Support"},
        {"role_name": "ContentEditor"},
        {"role_name": "Viewer"},
    ]
    roles = [Role(**data) for data in roles_data]
    session.add_all(roles)
    await session.flush()

    permissions = await session.execute(select(Permission))
    permissions = permissions.scalars().all()
    perm_by_resource = {p.resource: p for p in permissions}

    role_permissions_map = {
        "SuperAdmin": [p.permission_id for p in permissions],
        "Manager": [
            perm_by_resource["Users"].permission_id,
            perm_by_resource["Posts"].permission_id,
            perm_by_resource["Reports"].permission_id,
            perm_by_resource["Plans"].permission_id,
            perm_by_resource["Offers"].permission_id,
            perm_by_resource["Recharge"].permission_id,
            perm_by_resource["Sessions"].permission_id,
        ],
        "Support": [
            perm_by_resource["Users"].permission_id,
            perm_by_resource["Reports"].permission_id,
            perm_by_resource["Referral"].permission_id,
            perm_by_resource["Contact-form"].permission_id,
        ],
        "ContentEditor": [
            perm_by_resource["Content"].permission_id,
            perm_by_resource["Announcement"].permission_id,
            perm_by_resource["Offers"].permission_id,
        ],
        "Viewer": [
            perm_by_resource["Reports"].permission_id,
            perm_by_resource["Content"].permission_id,
        ],
    }

    role_permissions = []
    for role in roles:
        for pid in role_permissions_map.get(role.role_name, []):
            role_permissions.append(RolePermission(role_id=role.role_id, permission_id=pid))

    session.add_all(role_permissions)
    print("roles and RolePermissions seeded successfully.")


async def seed_admins(session: AsyncSession):
    """
    Seed administrator accounts for each role (3 admins per role).

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    existing_admins = await session.execute(select(Admin))
    existing_admins = existing_admins.scalars().all()

    if existing_admins:
        print("admins already exist, skipping seeding.")
        return

    print("seeding admins...")

    roles_result = await session.execute(select(Role))
    roles = roles_result.scalars().all()

    if not roles:
        print("no roles found. Please seed roles before running this.")
        return

    admins_to_add = []
    phone_base = 9000000000  

    for idx, role in enumerate(roles, start=1):
        for j in range(3):
            admin_number = (idx - 1) * 3 + j + 1
            admins_to_add.append(
                Admin(
                    name=f"{role.role_name}_Admin_{j+1}",
                    email=f"{role.role_name.lower()}_admin{j+1}@example.com",
                    phone_number=str(phone_base + admin_number),
                    role_id=role.role_id,
                )
            )

    session.add_all(admins_to_add)
    await session.flush()
    print(f"inserted {len(admins_to_add)} admins (3 per role).")


def random_referral_code(length=6):
    """
    Generate a random referral code of given length.

    Args:
        length (int): Length of the code. Defaults to 6.

    Returns:
        str: Uppercase alphanumeric referral code.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def random_phone_number():
    """
    Generate a random 10-digit phone number string starting with '9'.

    Returns:
        str: Random phone number.
    """
    return f"9{random.randint(100000000, 999999999)}"


def random_name():
    """
    Produce a random realistic-looking first and last name.

    Returns:
        str: Full name (first + last).
    """
    first_names = ["Aarav", "Vihaan", "Reyansh", "Isha", "Kavya", "Diya", "Rohan", "Aditi", "Aryan", "Meera"]
    last_names = ["Sharma", "Patel", "Reddy", "Iyer", "Kumar", "Bose", "Das", "Nair", "Menon", "Singh"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def random_id(length=8):
    """
    Generate a random alphanumeric identifier.

    Args:
        length (int): Length of the identifier. Defaults to 8.

    Returns:
        str: Uppercase alphanumeric identifier.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


async def seed_users(session: AsyncSession, count=50):
    """
    Seed a number of user records if the `User` table is empty.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.
        count (int): Number of users to create. Defaults to 50.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    existing_users = await session.execute(select(User))
    existing_users = existing_users.scalars().all()

    if existing_users:
        print("users already exist, skipping seeding.")
        return

    print(f"seeding {count} users...")

    users = []
    used_referrals = set()
    used_phones = set()

    for i in range(count):
        referral_code = random_referral_code()
        while referral_code in used_referrals:
            referral_code = random_referral_code()
        used_referrals.add(referral_code)

        phone = random_phone_number()
        while phone in used_phones:
            phone = random_phone_number()
        used_phones.add(phone)

        name = random_name()
        email = f"{name.lower().replace(' ', '_')}{i}@example.com"
        user_type = random.choice(list(["prepaid", "postpaid"]))
        status = random.choice(list(UserStatus)).value
        wallet_balance = round(random.uniform(0, 5000), 2)
        created_at = datetime.now()

        users.append(
            User(
                name=name,
                email=email,
                phone_number=phone,
                referral_code=referral_code,
                referee_code=random.choice(list(used_referrals)) if i > 0 else None,
                user_type=user_type,
                status=status,
                wallet_balance=wallet_balance,
                created_at=created_at,
                updated_at=created_at,
            )
        )

    session.add_all(users)
    await session.flush()
    print(f"successfully seeded {count} users.")


async def seed_user_archives(session: AsyncSession, count=5):
    """
    Seed user archive records if the `UserArchieve` table is empty.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.
        count (int): Number of archive entries to create. Defaults to 5.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    existing_archives = await session.execute(select(UserArchieve))
    existing_archives = existing_archives.scalars().all()

    if existing_archives:
        print("user Archives already exist, skipping seeding.")
        return

    print(f"seeding {count} user archives...")

    archives = []
    used_referrals = set()
    used_phones = set()

    for i in range(count):
        referral_code = random_referral_code()
        while referral_code in used_referrals:
            referral_code = random_referral_code()
        used_referrals.add(referral_code)

        phone = random_phone_number()
        while phone in used_phones:
            phone = random_phone_number()
        used_phones.add(phone)

        name = random_name()
        email = f"{name.lower().replace(' ', '_')}_arch{i}@example.com"
        user_type = random.choice(list(["prepaid", "postpaid"]))
        status = random.choice(list(UserStatus)).value
        wallet_balance = round(random.uniform(0, 5000), 2)
        created_at = datetime.now()
        deleted_at = datetime.now()

        archives.append(
            UserArchieve(
                name=name,
                email=email,
                phone_number=phone,
                referral_code=referral_code,
                referee_code=random.choice(list(used_referrals)) if i > 0 else None,
                user_type=user_type,
                status=status,
                wallet_balance=wallet_balance,
                created_at=created_at,
                deleted_at=deleted_at,
            )
        )

    session.add_all(archives)
    await session.flush()
    print(f"successfully seeded {count} user archives.")


async def seed_user_preferences(session: AsyncSession):
    """
    Create `UserPreference` records for users who don't yet have preferences.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding user preferences...")

    users_result = await session.execute(select(User))
    users = users_result.scalars().all()

    if not users:
        print("no users found. Please seed users first.")
        return

    existing_prefs_result = await session.execute(select(UserPreference))
    existing_prefs = existing_prefs_result.scalars().all()
    existing_user_ids = {pref.user_id for pref in existing_prefs}

    new_preferences = []
    for user in users:
        if user.user_id in existing_user_ids:
            continue  

        new_preferences.append(
            UserPreference(
                user_id=user.user_id,
                email_notification=random.choice([True, False]),
                sms_notification=random.choice([True, False]),
                marketing_communication=random.choice([True, False]),
                recharge_remainders=random.choice([True, False]),
                promotional_offers=random.choice([True, False]),
                transactional_alerts=random.choice([True, False]),
                data_analytics=random.choice([True, False]),
                third_party_integrations=random.choice([True, False]),
            )
        )

    if not new_preferences:
        print("all users already have preferences, skipping seeding.")
        return

    session.add_all(new_preferences)
    await session.flush()
    print(f"seeded preferences for {len(new_preferences)} new users.")


async def seed_plan_groups_and_plans(session: AsyncSession):
    """
    Seed `PlanGroup` and associated `Plan` records.

    Creates several plan groups and multiple plans per group. Skips seeding
    if plan groups already exist.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding PlanGroups and Plans...")

    existing_groups = await session.execute(select(PlanGroup))
    existing_groups = existing_groups.scalars().all()

    if existing_groups:
        print("plan groups already exist, skipping seeding.")
        return

    group_names = [
        "Unlimited 5G",
        "International Roaming",
        "Data Booster",
        "Family Pack",
        "Corporate Bundle",
    ]

    plan_groups = [PlanGroup(group_name=name) for name in group_names]
    session.add_all(plan_groups)
    await session.flush()  

    plans_to_add = []
    for group in plan_groups:
        for i in range(1, 6):  
            plan_type = random.choice(list(PlanType)).value
            status = random.choice(list(PlanStatus))
            plan_name = f"{group.group_name} Plan {i}"

            plans_to_add.append(
                Plan(
                    plan_name=plan_name,
                    validity=random.choice([28, 56, 84, 90, 180]),
                    most_popular=random.choice([True, False]),
                    plan_type=plan_type,
                    group_id=group.group_id,
                    description=f"{plan_name} offering {plan_type} benefits.",
                    criteria={
                        "data": f"{random.choice([1, 1.5, 2, 3, 5])}GB/day",
                        "voice": random.choice(["Unlimited", "1000 mins"]),
                        "sms": f"{random.choice([100, 200, 300])} SMS/day",
                    },
                    created_by=random.randint(1, 5), 
                    price=random.choice([199, 299, 399, 499, 599, 699, 899]),
                    status=status,
                )
            )

    session.add_all(plans_to_add)
    await session.flush()
    print(f"seeded {len(plan_groups)} plan groups and {len(plans_to_add)} plans.")


async def seed_offer_types_and_offers(session: AsyncSession):
    """
    Seed `OfferType` and `Offer` records with example data.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding OfferTypes and Offers...")

    existing_types = await session.execute(select(OfferType))
    existing_types = existing_types.scalars().all()

    if existing_types:
        print("Offer types already exist, skipping seeding.")
        return

    offer_type_names = [
        "Festive Offers",
        "Cashback Offers",
        "Data Bonus Offers",
        "Loyalty Rewards",
    ]

    offer_types = [OfferType(offer_type_name=name) for name in offer_type_names]
    session.add_all(offer_types)
    await session.flush()  

    offers_to_add = []
    for offer_type in offer_types:
        for i in range(1, 6):  
            offer_name = f"{offer_type.offer_type_name} {i}"
            validity = random.choice([7, 14, 28, 56, 84, 90])
            is_special = random.choice([True, False])
            status = random.choice(list(OfferStatus)).value
            price_discount = random.choice([10, 15, 20, 25, 30])
            extra_data = random.choice([None, "1GB", "2GB", "3GB"])

            offers_to_add.append(
                Offer(
                    offer_name=offer_name,
                    offer_validity=validity,
                    offer_type_id=offer_type.offer_type_id,
                    is_special=is_special,
                    criteria={
                        "discount_percent": price_discount,
                        "extra_data": extra_data,
                        "min_recharge": random.choice([99, 199, 299, 399]),
                    },
                    description=f"{offer_name} gives {price_discount}% discount with {extra_data or 'no extra data'}.",
                    created_by=random.randint(1, 5),  
                    status=status,
                )
            )

    session.add_all(offers_to_add)
    await session.flush()
    print(f"seeded {len(offer_types)} offer types and {len(offers_to_add)} offers.")


async def seed_autopay(session: AsyncSession):
    """
    Seed AutoPay entries for existing users and plans.

    Generates 2–5 AutoPay entries per user and skips if AutoPay records
    already exist.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding AutoPay entries...")

    users_result = await session.execute(select(User))
    users = users_result.scalars().all()

    plans_result = await session.execute(select(Plan))
    plans = plans_result.scalars().all()

    if not users:
        print("no users found. Please seed users first.")
        return

    if not plans:
        print("no plans found. Please seed plans first.")
        return

    existing_autopays = await session.execute(select(AutoPay))
    existing_autopays = existing_autopays.scalars().all()
    if existing_autopays:
        print("AutoPay entries already exist, skipping seeding.")
        return

    autopay_entries = []

    for user in users:
        num_autopays = random.randint(2, 5)  
        selected_plans = random.sample(plans, min(num_autopays, len(plans)))

        for plan in selected_plans:
            status = random.choices(["enabled", "disabled"], weights=[0.8, 0.2])[0]
            tag = random.choice(["onetime", "regular"])
            next_due_date = datetime.now() + timedelta(days=random.randint(7, 60))

            autopay_entries.append(
                AutoPay(
                    user_id=user.user_id,
                    plan_id=plan.plan_id,
                    status=status,
                    phone_number=user.phone_number,
                    tag=tag,
                    next_due_date=next_due_date,
                )
            )

    session.add_all(autopay_entries)
    await session.flush()
    print(f"seeded {len(autopay_entries)} AutoPay entries ({len(users)} users × 2–5 plans each).")


async def seed_current_active_plans(session: AsyncSession):
    """
    Seed `CurrentActivePlan` records for users.

    Creates 2–4 active/current plans per user with randomized validity and
    status. Skips seeding if entries already exist.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding Current Active Plans...")

    existing = await session.execute(select(CurrentActivePlan))
    existing = existing.scalars().all()

    if existing:
        print("CurrentActivePlans already exist, skipping seeding.")
        return

    users_result = await session.execute(select(User))
    users = users_result.scalars().all()

    plans_result = await session.execute(select(Plan))
    plans = plans_result.scalars().all()

    if not users:
        print("no users found. please seed users first.")
        return

    if not plans:
        print("no plans found. please seed plans first.")
        return

    entries_to_add = []
    now = datetime.now()

    for user in users:
        num_plans = random.randint(2, 4)
        selected_plans = random.sample(plans, min(num_plans, len(plans)))

        for plan in selected_plans:
            status = random.choice(list(CurrentPlanStatus)).value

            start_offset = random.randint(-60, 30) 
            valid_from = now + timedelta(days=start_offset)
            valid_to = valid_from + timedelta(days=plan.validity or 28)

            if status == CurrentPlanStatus.queued.value:
                valid_from = now + timedelta(days=random.randint(1, 15))
                valid_to = valid_from + timedelta(days=plan.validity or 28)

            entries_to_add.append(
                CurrentActivePlan(
                    user_id=user.user_id,
                    plan_id=plan.plan_id,
                    phone_number=user.phone_number,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    status=status,
                )
            )

    session.add_all(entries_to_add)
    await session.flush()
    print(f"seeded {len(entries_to_add)} CurrentActivePlan entries ({len(users)} users × 2–4 plans each).")


async def seed_backups(session: AsyncSession):
    """
    Seed example `Backup` records to simulate backup metadata.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding Backup data...")

    existing = await session.execute(select(Backup))
    existing_backups = existing.scalars().all()

    if existing_backups:
        print("backups already exist, skipping seeding.")
        return

    backup_targets = ["products", "orders", "users", "sessions", "plans"]
    backup_entries = []

    for i in range(10):
        data_type = random.choice(backup_targets)

        timestamp = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        snapshot_name = f"backup_{timestamp.strftime('%Y_%m_%d_%H_%M')}"
        storage_url = f"s3://my-backups/{snapshot_name}"

        status = random.choices(["success", "failed"], weights=[0.8, 0.2])[0]
        size_mb = str(random.randint(100, 1000))  
        desc = f"{data_type.capitalize()} backup created on {timestamp.strftime('%Y-%m-%d %H:%M')}."
        details = {
            "file_count": random.randint(5, 50),
            "compressed": random.choice([True, False]),
            "duration_sec": random.randint(20, 300),
            "region": random.choice(["ap-south-1", "us-east-1", "eu-west-1"]),
        }

        backup_entries.append(
            Backup(
                backup_id=random_id(10),
                backup_data=data_type,
                snapshot_name=snapshot_name,
                storage_url=storage_url,
                backup_status=status,
                size_mb=size_mb,
                description=desc,
                details=details,
                created_by=random.randint(1, 5),
            )
        )

    session.add_all(backup_entries)
    await session.flush()
    print(f"seeded {len(backup_entries)} backup records successfully.")


async def seed_transactions(session: AsyncSession):
    """
    Seed example `Transaction` records to simulate application transactions.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding Transactions...")

    existing = await session.execute(select(Transaction))
    existing_txns = existing.scalars().all()

    if existing_txns:
        print("transactions already exist, skipping seeding.")
        return

    users = (await session.execute(select(User))).scalars().all()
    plans = (await session.execute(select(Plan))).scalars().all()
    offers = (await session.execute(select(Offer))).scalars().all()

    if not users:
        print("no users found. Please seed users first.")
        return
    if not plans:
        print("no plans found. Please seed plans first.")
        return
    if not offers:
        print("no offers found. Please seed offers first.")
        return

    transactions_to_add = []
    for _ in range(50):
        user = random.choice(users)
        plan = random.choice(plans)
        offer = random.choice(offers)

        category = random.choice(list(TransactionCategory)).value
        txn_type = random.choice(list(TransactionType)).value
        service_type = random.choice(list(ServiceType)).value
        source = random.choice(list(TransactionSource)).value
        status = random.choices(
            [TransactionStatus.success, TransactionStatus.failed, TransactionStatus.pending],
            weights=[0.75, 0.15, 0.10],
        )[0].value
        payment_method = random.choice(list(PaymentMethod)).value

        if category == TransactionCategory.wallet.value:
            amount = Decimal(random.randint(50, 5000))
        else:
            amount = Decimal(random.randint(99, 1499))

        txn = Transaction(
            user_id=user.user_id,
            category=category,
            txn_type=txn_type,
            amount=amount,
            service_type=service_type,
            plan_id=plan.plan_id if category == TransactionCategory.service.value else None,
            offer_id=offer.offer_id if random.random() > 0.5 else None,
            from_phone_number=user.phone_number,
            to_phone_number=user.phone_number if random.random() > 0.3 else None,
            source=source,
            status=status,
            payment_method=payment_method,
            payment_transaction_id=f"TXN{random.randint(10000000, 99999999)}",
        )

        transactions_to_add.append(txn)

    session.add_all(transactions_to_add)
    await session.flush()
    print(f"seeded {len(transactions_to_add)} transactions successfully.")


async def seed_referral_rewards(session: AsyncSession):
    """
    Create `ReferralReward` records based on existing users' referral codes.

    Args:
        session (AsyncSession): Async SQLAlchemy session used for DB operations.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If DB operations fail.
    """
    print("seeding ReferralRewards...")

    existing = await session.execute(select(ReferralReward))
    existing_rewards = existing.scalars().all()

    if existing_rewards:
        print("referral rewards already exist, skipping seeding.")
        return

    users_result = await session.execute(select(User))
    users = users_result.scalars().all()
    if not users:
        print("no users found. please seed users first.")
        return

    referral_code_map = {u.referral_code: u for u in users if u.referral_code}

    rewards_to_add = []
    for user in users:
        if user.referee_code and user.referee_code in referral_code_map:
            referrer = referral_code_map[user.referee_code]

            if referrer.user_id == user.user_id:
                continue

            status = random.choice(list(ReferralRewardStatus)).value
            reward_amount = Decimal(random.choice([50, 75, 100, 125, 150]))
            claimed_at = (
                datetime.now() - timedelta(days=random.randint(1, 30))
                if status == ReferralRewardStatus.earned.value
                else None
            )

            rewards_to_add.append(
                ReferralReward(
                    referrer_id=referrer.user_id,
                    referred_id=user.user_id,
                    reward_amount=reward_amount,
                    status=status,
                    claimed_at=claimed_at,
                )
            )

    if not rewards_to_add:
        print("no referral relationships found among users.")
        return

    session.add_all(rewards_to_add)
    await session.flush()
    print(f"seeded {len(rewards_to_add)} referral rewards successfully.")


async def seed_all():
    """
    Run the full seeding pipeline against a local AsyncSessionLocal.

    This convenience function runs all individual seeders in a single
    transaction and commits when complete.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If any seeding step fails.
    """
    async with AsyncSessionLocal() as session:
        await seed_permissions(session)
        await seed_roles_and_role_permissions(session)
        await seed_admins(session)
        await seed_users(session)
        await seed_user_archives(session)
        await seed_user_preferences(session)
        await seed_plan_groups_and_plans(session)
        await seed_offer_types_and_offers(session)
        await seed_autopay(session)
        await seed_current_active_plans(session)
        await seed_backups(session)
        await seed_transactions(session)
        await seed_referral_rewards(session)
        await session.commit()
        print("database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_all())
