from cmath import e
import json
import math
from itertools import product
import re
from urllib import response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from uritemplate import partial
from cart.serializers import CheckOutSerializer, CartSerializer
from store.serializers import *
from django.contrib.auth.models import User
from cart.models import CheckOut, Cart
from store.models import ProductPrice, ProductOffer, Store
from product_list.models import *
from product_list.serializers import ProductSerializer
from store.serializers import ProductPriceSerializer
from accounts.serializers import UserCreateSerializer
from rest_framework import status
import datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
import io
from rest_framework.permissions import IsAuthenticated  # HELPER FUNCTIONS
from django.contrib.auth import get_user_model

from accounts.models import *

# Create your models here.
User = get_user_model()
# get checkout with upon request data and open


def getCheckout(data):
    print(data)
    checkout_data = {
        "user": data["user_id"],  # edit with the current user
        "store": data["store_id"],  # sent with request
    }
    # if the checkout is not eisted => empty & none
    checkout = CheckOut.objects.filter(
        user_id=checkout_data["user"], store_id=checkout_data["store"], state="open"
    ).first()

    return checkout


# NEED EDIT
# view all checkouts and its order details
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def ListAllCheckouts(request):

    data = request.query_params.get("owner_id")

    print(f"dataddd===={data}")
    checkout_data = {
        "user": data,  # edit with the current user
    }

    store = Store.objects.filter(user_account_id=checkout_data["user"]).first()

    checkout = CheckOut.objects.filter(store_id=store.id)
    Checkout = CheckOutSerializer(checkout, many=True)
    print(Checkout)
    api_return = {"Checkout": []}

    for order in Checkout.data:
        # the layout of each checkout
        orderDetails = {"order_detail": [], "customer": [], "cart": [], "total": []}

        orderDetails["order_detail"].append(order)

        customer = User.objects.filter(id=order["user"]).first()
        Customer = UserCreateSerializer(customer, many=False)
        # UserCreateSerializer
        orderDetails["customer"].append(Customer.data)

        cart = Cart.objects.filter(order_id=order["id"])
        CartSer = CartSerializer(cart, many=True)

        total = 0

        for item in CartSer.data:
            # the lay out of each product in the cart
            temp_cart = {
                "cart_details": [],  # from cart
                "product_details": [],  # from Product
                "price": [],  # from ProductPrice
                "offer": [],  # from ProductOffer
                "price_offer": [],  # from calculated
            }
            # get cart details [orderid, quantity, product price id ]
            temp_cart["cart_details"].append(item)
            offer = 0
            price = 0
            # get product that has the same product price exist in the cart and the same store id in the checkout
            product_price = get_object_or_404(
                ProductPrice, store_id=order["store"], id=item["product"]
            )
            temp_cart["price"].append(product_price.price)
            # get the produt details [id, name, price befor offer, brand_id, category_id]
            product_detail = Product.objects.filter(id=product_price.product_id).first()
            product_ser = ProductSerializer(product_detail, many=False)

            temp_cart["product_details"].append(product_ser.data)
            # get the offer if exist and calculate it
            try:
                product_offer = get_object_or_404(
                    ProductOffer, price_id=product_price.id
                )
                offer = product_price.price * (1 - (product_offer.offer / 100))
            except:
                # if it doesnt exist let it be 0
                offer = 0

            # add the offer to the cart
            temp_cart["offer"].append(offer)
            # calculate the price after the offer and add it to the total
            # you can add field price which has the price after the offer if you like
            price = product_price.price - offer
            temp_cart["price_offer"].append(price)
            total += price * item["quantity"]
            # add the current cart to the checkout
            orderDetails["cart"].append(temp_cart)

        orderDetails["total"].append(total)
        api_return["Checkout"].append(orderDetails)
    return Response(api_return)


"""
view the checkout data:
{
    checkout:{
        order_details:{
            id:
            date:
            state:
            store:
            user:
        }
    }
}
"""


def viewCheckout(request):
    # checkout
    checkout = getCheckout(request.query_params)
    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)
    Checkout = CheckOutSerializer(checkout, many=False)
    # validation if there is no Checkout => why to continue?
    api_return = {"checkout": {}}
    orderDetails = {"order_details": {}, "carts": [], "total": 0}

    # carts in the checkout order
    order = Checkout.data
    orderDetails["order_details"] = order
    cart = Cart.objects.filter(order_id=order["id"])
    CartSer = CartSerializer(cart, many=True)

    total = 0
    for item in CartSer.data:
        #! start for loop
        # the lay out of each product in the cart
        temp_cart = {
            "cart_details": {},  # from cart
            "product_details": [],  # from Product
            "price": 0,  # from ProductPrice
            "offer": 0,  # from ProductOffer
            "price_after_offer": 0,  # from calculated
        }
        # get cart details [orderid, quantity, product price id ]
        temp_cart["cart_details"] = item
        offer = 0
        price = 0
        # get product that has the same product price exist in the cart and the same store id in the checkout
        product_price = get_object_or_404(
            ProductPrice, store_id=order["store"], id=item["product"]
        )
        temp_cart["price"] = product_price.price
        # get the produt details [id, name, price befor offer, brand_id, category_id]
        product_detail = Product.objects.filter(id=product_price.product_id).first()
        product_ser = ProductSerializer(product_detail, many=False)

        #! changes in the serialization => lead to changes in the dictionary
        category_id = product_ser.data["category"]["id"]
        category = Category.objects.get(id=category_id)

        temp_cart["product_details"] = product_ser.data

        # get the offer if exist and calculate it
        try:
            product_offer = get_object_or_404(ProductOffer, price_id=product_price.id)
            offer = product_price.price * (1 - (product_offer.offer / 100))
        except:
            # if it doesnt exist let it be 0
            offer = 0

        # add the offer to the cart
        temp_cart["offer"] = offer
        # calculate the price after the offer and add it to the total
        # you can add field price which has the price after the offer if you like
        price = float(product_price.price - offer)
        temp_cart["price_after_offer"] = price
        total += price * item["quantity"]
        # add the current cart to the checkout
        orderDetails["carts"].append(temp_cart)

        #! end for loop

    orderDetails["total"] = total

    api_return["checkout"] = orderDetails

    return Response(api_return, status=status.HTTP_200_OK)


""" 
    - create an empty checkout in the first to add the products
        - create the product and add it to the cart 
    - add products to the existed checkout  
        - add product to the checkout if the product not existed
        - update the quatity of the product if it's existed in the cart
    
"""

# if pending => no add
# @api_view(["POST"])


def addItemInCart(request):  # [/]
    # check if the checkout is exist
    data = request.data

    # checkout => open , current user , in the current store => order id
    checkout_data = {
        "user": data["user_id"],  # edit with the current user
        "store": data["store_id"],  # sent with request
        "orderDate": datetime.datetime.now(),
    }

    checkout, created = CheckOut.objects.get_or_create(
        user_id=checkout_data["user"], store_id=checkout_data["store"], state="open"
    )
    # if the checkout is created we add the date with the current time stamp
    if created:

        checkout.orderDate = datetime.datetime.now()
        checkout.save()

    # if the product exist we add its quatity to the old quatity if not we create a new one
    quantity = data["quantity"]
    # get the product actual price ID
    product_price = get_object_or_404(
        ProductPrice, store_id=data["store_id"], product_id=data["product_id"]
    )
    try:  # if there is an initiated cart item
        # cart contains product price not product ID
        old_carts = Cart.objects.get(order_id=checkout.id, product=product_price.id)
        print("====>", {old_carts})
        quantity += old_carts.quantity
        old_carts.quantity = quantity
        old_carts.save()
        CartSer = CartSerializer(old_carts, many=False)
    except:  # if not => create a new one
        cart_data = {
            # this checkout(open checkout) should be unique for (current user, currentstore)
            "order": checkout.id,
            "product": product_price.id,
            "quantity": quantity,
        }
        CartSer = CartSerializer(data=cart_data)
        if CartSer.is_valid():
            CartSer.save()

    # return cart data
    #   {
    #   cart item id =>     (cart_id)
    #   checkout id =>      (order_id)
    #   product price id => (product_price_id)
    #   quantity =>         (quantity)
    #   }

    return Response(CartSer.data, status=status.HTTP_200_OK)


# update the checkout state only to 'pending' or 'done'
# status code is REQUIRED as return
@api_view(["PUT"])
def updateCheckoutState(request):
    data = request.data
    print("DATAAAA:", data)
    state = {"state": data["state"]}
    checkout_data = {
        "user": data["user_id"],  # edit with the current user
        "store": data["store_id"],  # sent with request
        "orderDate": datetime.datetime.now(),
    }
    checkout = CheckOut.objects.filter(
        user_id=checkout_data["user"], store=checkout_data["store"], state="open"
    ).first()

    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)

    api_return = {
        "state": data["state"],
        "payment": data["payment"],
        "orderDate": checkout_data["orderDate"],
    }

    Checkout = CheckOutSerializer(instance=checkout, data=api_return, partial=True)
    if Checkout.is_valid():
        Checkout.save()
    return Response(Checkout.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def updatePaymentMethod(request):
    data = request.data
    payment = {"payment": data["payment"]}
    checkout_data = {
        "user": data["user_id"],  # edit with the current user
        "store": data["store_id"],  # sent with request
    }
    checkout = CheckOut.objects.filter(
        user_id=checkout_data["user"], store=checkout_data["store"], state="open"
    ).first()

    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)

    Checkout = CheckOutSerializer(instance=checkout, data=payment, partial=True)
    if Checkout.is_valid():
        Checkout.save()

    return Response(Checkout.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def OwnerUpdateCheckoutState(request):
    data = request.data
    checkout_data = {
        "user": data["owner_id"],  # edit with the current user
        "orderID": data["order_id"],
    }
    store = Store.objects.filter(user_account_id=checkout_data["user"]).first()
    checkout = CheckOut.objects.filter(
        id=checkout_data["orderID"], store_id=store.id
    ).first()

    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)

    update = {"state": "done"}

    Checkout = CheckOutSerializer(instance=checkout, data=update, partial=True)
    if Checkout.is_valid():
        Checkout.save()
    return Response(Checkout.data, status=status.HTTP_200_OK)


# update the item quatity
# @api_view(["PUT"])


def updateCart(request):
    data = request.data
    newQuantity = {"quantity": data["quantity"]}

    checkout = getCheckout(data)
    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)
    product_price = get_object_or_404(
        ProductPrice, store_id=data["store_id"], product_id=data["product_id"]
    )
    cart = Cart.objects.get(order_id=checkout.id, product_id=product_price.id)

    if newQuantity["quantity"] < 1:
        cart.delete()
        return Response("Order item succsesfully delete!", status=status.HTTP_200_OK)
    else:
        cartSer = CartSerializer(instance=cart, data=newQuantity, partial=True)
        if cartSer.is_valid():
            cartSer.save()
        return Response(cartSer.data, status=status.HTTP_200_OK)


# NEED EDIT
# delete order item from checkout cart
# @api_view(["DELETE"])
def deleteCart(request):
    data = request.data
    checkout_data = {
        "user": data["user_id"],  # edit with the current user
        "store": data["store_id"],  # sent with request
    }
    checkout = CheckOut.objects.filter(
        user_id=checkout_data["user"], store=checkout_data["store"], state="open"
    ).first()

    if not checkout:
        return Response(status=status.HTTP_404_NOT_FOUND)

    product_price = get_object_or_404(
        ProductPrice, store_id=data["store_id"], product_id=data["product_id"]
    )
    cart = Cart.objects.get(order_id=checkout.id, product=product_price.id)
    cart.delete()
    return Response("Order item succsesfully delete!", status=status.HTTP_200_OK)


# delete checkout
@api_view(["DELETE"])
def deleteCheckout(request, pk):
    checkout = CheckOut.objects.get(id=pk)
    checkout.delete()
    return Response("Checkout succsesfully delete!", status=status.HTTP_200_OK)


@api_view(["GET", "PUT", "DELETE", "POST"])
def cart_view(request):

    if request.method == "GET":
        return viewCheckout(request)

    elif request.method == "PUT":
        return updateCart(request)

    elif request.method == "POST":
        return addItemInCart(request)

    elif request.method == "DELETE":
        return deleteCart(request)


class CartView(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()


# <|--- general views ---|>

# <-- getting a list of products -->


@api_view(["GET"])
def getPriceList(request):
    product_list = request.query_params.getlist("product_store[]", None)
    product_list_dic = []
    for item in product_list:
        item = json.loads(item)
        product_price = ProductPrice.objects.get(
            product=item["product"], store=item["store"]
        )
        product_list_dic.append(product_price)
    product_price_serializer = ProductPriceSerializer(product_list_dic, many=True)

    return Response(product_price_serializer.data)


# <-- moving the local list to database -->
"""
1. get user_id & list of [{store_id & [{product_id&quantity},{..}]} ,{...},{...}]
2. loop through each store_id [ loop through ]
    => if there is an open checkout for that store (user_id & store_id)
        => if there is a similar cart (store_id & product_id ) in it
            => don't add it
        => if no similar product in that checkout => add it
    => if there is no open checkout 
        => create a new one & add products in it

"""
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def moveLocalToDB(request):
    data = request.data
    user_id = data["user_id"]

    """<-- for each store -->"""
    for cart in data["list_of_carts"]:
        cart_item = {}
        cart_item["store_id"] = cart[0]["store"]["id"]
        store_id = cart[0]["store"]["id"]
        checkout, created = CheckOut.objects.get_or_create(
            user_id=user_id, store_id=store_id, state="open"
        )

        """<--for each product in the store-->"""
        for item in cart:
            product_id = item["product"]["id"]
            quantity = item["quantity"]
            product_price = ProductPrice.objects.get(product=product_id, store=store_id)
            cart, created = Cart.objects.get_or_create(
                product=product_price,
                order_id=checkout.id,
                defaults={"quantity": quantity},
            )

    return Response(status=status.HTTP_200_OK)
