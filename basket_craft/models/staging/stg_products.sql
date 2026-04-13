with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
    select
        product_id,
        product_name,
        cast(price_usd as decimal(10, 2)) as product_price

    from source
)

select * from renamed
