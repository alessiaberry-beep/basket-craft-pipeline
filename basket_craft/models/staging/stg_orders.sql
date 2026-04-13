with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        order_id,
        user_id as customer_id,
        cast(created_at as timestamp) as order_date,
        cast(price_usd as decimal(12, 2)) as order_total

    from source
)

select * from renamed
