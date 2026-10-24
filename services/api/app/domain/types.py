from sqlalchemy import BigInteger, Integer

# SQLite only autoincrements INTEGER primary keys; MySQL uses BIGINT.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
