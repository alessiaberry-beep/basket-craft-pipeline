with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        order_item_id,
        order_id,
        product_id,
        cast(price_usd as decimal(12, 2)) as item_price

    from source
)

select * from renamed
