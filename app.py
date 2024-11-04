from flask import Flask, render_template, redirect, url_for, session, request, flash
from extensions import db, login_manager

from flask_login import login_required, current_user
import stripe

app = Flask(__name__)
app.config['SECRET_KEY'] = '000xxx111AAA'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Stripe configuration
stripe.api_key = "the_stripe_secret_key"

# Database models
from models import User, Product, Order

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    products = Product.query.filter(Product.id.in_(cart_items.keys())).all()
    total = sum(item['price'] * item['quantity'] for item in cart_items.values())
    return render_template('cart.html', products=products, total=total)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = session.get('cart', {})
    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {'price': product.price, 'quantity': 1}
    session['cart'] = cart
    flash(f'{product.name} added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = session.get('cart', {})
    if request.method == 'POST':
        amount = int(sum(item['price'] * item['quantity'] for item in cart_items.values()) * 100)
        customer = stripe.Customer.create(email=current_user.email, source=request.form['stripeToken'])
        stripe.Charge.create(customer=customer.id, amount=amount, currency='usd', description='Ecommerce Purchase')
        
        # Clear cart and save order
        session.pop('cart')
        flash("Payment successful!", 'success')
        return redirect(url_for('home'))
    return render_template('checkout.html', key="your_stripe_publishable_key")

if __name__ == '__main__':
    app.run(debug=True)
    with app.app_context():
    db.create_all()

