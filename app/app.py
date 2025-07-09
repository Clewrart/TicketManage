from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from app.models import db, User, TrainTicket, FlightTicket, MetroCard
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ticgsy:ticGSY123@47.96.10.165:3306/ticket'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

# 用户认证相关路由
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        username = request.form['username']
        
        if User.query.filter_by(Phone=phone).first():
            flash('手机号已注册', 'danger')
            return redirect(url_for('register'))
        
        user = User(Phone=phone, UsrName=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        user = User.query.filter_by(Phone=phone).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.usrID
            session['username'] = user.UsrName
            flash('登录成功', 'success')
            return redirect(url_for('dashboard'))
        
        flash('手机号或密码错误', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已退出登录', 'info')
    return redirect(url_for('login'))

# 仪表盘
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # 统计信息
    train_stats = db.session.query(
        db.func.sum(TrainTicket.price).label('total_price'),
        db.func.sum(TrainTicket.distance).label('total_distance')
    ).filter_by(user_id=user_id).first()
    
    flight_stats = db.session.query(
        db.func.sum(FlightTicket.price).label('total_price'),
        db.func.sum(FlightTicket.distance).label('total_distance')
    ).filter_by(user_id=user_id).first()
    metrocard_count = MetroCard.query.filter_by(user_id=user_id).count()
    
    return render_template('dashboard.html',
                           train_stats=train_stats,
                           flight_stats=flight_stats,
                           metrocard_count=metrocard_count
                          )

@app.route('/train-tickets')
def train_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 只选择需要的字段，排除 ticket_photo
    tickets = db.session.query(
        TrainTicket.TrainRecordID,
        TrainTicket.train_number,
        TrainTicket.departure_date,
        TrainTicket.departure_time,
        TrainTicket.arrival_station,
        TrainTicket.departure_station,
        TrainTicket.price
    ).filter_by(user_id=session['user_id']).order_by(
        TrainTicket.departure_date.desc(),
        TrainTicket.departure_time.desc()
    ).all()
    return render_template('tickets/train_tickets.html', tickets=tickets)

@app.route('/train-tickets/add', methods=['GET', 'POST'])
def add_train_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            ticket = TrainTicket(
                user_id=session['user_id'],
                train_number=request.form['train_number'],
                departure_date=datetime.strptime(request.form['departure_date'], '%Y-%m-%d').date(),
                departure_time=datetime.strptime(request.form['departure_time'], '%H:%M').time(),
                arrival_date=datetime.strptime(request.form['arrival_date'], '%Y-%m-%d').date(),
                arrival_time=datetime.strptime(request.form['arrival_time'], '%H:%M').time(),
                departure_station=request.form['departure_station'],
                arrival_station=request.form['arrival_station'],
                ticket_class=request.form['ticket_class'],
                seat_number=request.form['seat_number'],
                price=float(request.form['price']),
                distance=float(request.form['distance']) if request.form['distance'] else None,
                railwaycom=request.form['railwaycom'],
                train_model=request.form['train_model'],
                train_code=request.form['train_code']
            )
            
            # 处理图片上传并转为 Base64
            if 'ticket_photo' in request.files:
                photo_file = request.files['ticket_photo']
                if photo_file.filename != '':
                    # 读取图片文件并转换为 Base64
                    photo_data = photo_file.read()
                    base64_photo = base64.b64encode(photo_data).decode('utf-8')
                    ticket.ticket_photo = base64_photo
            
            db.session.add(ticket)
            db.session.commit()
            flash('火车票添加成功', 'success')
            return redirect(url_for('train_tickets'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('tickets/add_train_ticket.html')

@app.route('/train-tickets/<int:id>')
def view_train_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = TrainTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    return render_template('tickets/view_train_ticket.html', ticket=ticket)

@app.route('/train-tickets/<int:id>/edit', methods=['GET', 'POST'])
def edit_train_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = TrainTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    if request.method == 'POST':
        try:
            ticket.train_number = request.form['train_number']
            ticket.departure_date = datetime.strptime(request.form['departure_date'], '%Y-%m-%d').date()
            ticket.departure_time = datetime.strptime(request.form['departure_time'], '%H:%M').time()
            ticket.arrival_date = datetime.strptime(request.form['arrival_date'], '%Y-%m-%d').date()
            ticket.arrival_time = datetime.strptime(request.form['arrival_time'], '%H:%M').time()
            ticket.go_deltatime = request.form['go_deltatime']
            ticket.arrive_deltatime = request.form['arrive_deltatime']
            ticket.departure_station = request.form['departure_station']
            ticket.arrival_station = request.form['arrival_station']
            ticket.ticket_class = request.form['ticket_class']
            ticket.seat_number = request.form['seat_number']
            ticket.price = float(request.form['price'])
            ticket.distance = float(request.form['distance']) if request.form['distance'] else None
            ticket.railwaycom = request.form['railwaycom']
            ticket.train_model = request.form['train_model']
            ticket.train_code = request.form['train_code']
            
            if 'ticket_photo' in request.files and request.files['ticket_photo'].filename != '':
                ticket.set_ticket_photo(request.files['ticket_photo'])
            
            db.session.commit()
            flash('火车票更新成功', 'success')
            return redirect(url_for('view_train_ticket', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('tickets/edit_train_ticket.html', ticket=ticket)

@app.route('/train-tickets/<int:id>/delete', methods=['POST'])
def delete_train_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = TrainTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        flash('火车票删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('train_tickets'))

# 飞机票CRUD (与火车票类似)
# @app.route('/flight-tickets')
# def flight_tickets():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     tickets = FlightTicket.query.filter_by(user_id=session['user_id']).order_by(
#         FlightTicket.scheduled_departure_date.desc(),
#         FlightTicket.scheduled_departure_time.desc()
#     ).all()
#     return render_template('tickets/flight_tickets.html', tickets=tickets)

@app.route('/flight-tickets')
def flight_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 只选择需要的字段，排除 ticket_image
    tickets = db.session.query(
        FlightTicket.flightRecordID,
        FlightTicket.flight_number,
        FlightTicket.scheduled_departure_date,
        FlightTicket.scheduled_departure_time,
        FlightTicket.departure_airport,
        FlightTicket.departure_airport_code,
        FlightTicket.arrival_airport,
        FlightTicket.arrival_airport_code,
        FlightTicket.airline,
        FlightTicket.airline_code,

        FlightTicket.price
    ).filter_by(user_id=session['user_id']).order_by(
        FlightTicket.scheduled_departure_date.desc(),
        FlightTicket.scheduled_departure_time.desc()
    ).all()
    return render_template('tickets/flight_tickets.html', tickets=tickets)

@app.route('/flight-tickets/add', methods=['GET', 'POST'])
def add_flight_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            ticket = FlightTicket(
                user_id=session['user_id'],
                flight_number=request.form['flight_number'],
                cabin_class=request.form['cabin_class'],
                seat_number=request.form['seat_number'],
                price=float(request.form['price']),
                airline=request.form['airline'],
                airline_code=request.form['airline_code'],
                departure_airport=request.form['departure_airport'],
                departure_airport_code=request.form['departure_airport_code'],
                departure_terminal=request.form['departure_terminal'],
                boarding_gate=request.form['boarding_gate'],
                arrival_airport=request.form['arrival_airport'],
                arrival_airport_code=request.form['arrival_airport_code'],
                scheduled_departure_date=datetime.strptime(request.form['scheduled_departure_date'], '%Y-%m-%d').date(),
                scheduled_departure_time=datetime.strptime(request.form['scheduled_departure_time'], '%H:%M').time(),
                scheduled_arrival_date=datetime.strptime(request.form['scheduled_arrival_date'], '%Y-%m-%d').date(),
                scheduled_arrival_time=datetime.strptime(request.form['scheduled_arrival_time'], '%H:%M').time(),
                departure_delay=request.form['departure_delay'],
                arrival_delay=request.form['arrival_delay'],
                aircraft_type=request.form['aircraft_type'],
                registration_number=request.form['registration_number'],
                has_baggage_check=request.form['has_baggage_check'],
                departure_runway=request.form['departure_runway'],
                arrival_runway=request.form['arrival_runway'],
                etkt_number=request.form['etkt_number'],
                remarks=request.form['remarks'],
                distance=float(request.form['distance']) if request.form['distance'] else None
            )
            
            # 处理图片上传并转为 Base64
            if 'ticket_image' in request.files:
                photo_file = request.files['ticket_image']
                if photo_file.filename != '':
                    # 读取图片文件并转换为 Base64
                    photo_data = photo_file.read()
                    base64_photo = base64.b64encode(photo_data).decode('utf-8')
                    ticket.ticket_image = base64_photo
            
            db.session.add(ticket)
            db.session.commit()
            flash('机票添加成功', 'success')
            return redirect(url_for('flight_tickets'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('tickets/add_flight_ticket.html')

@app.route('/flight-tickets/<int:id>')
def view_flight_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = FlightTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    return render_template('tickets/view_flight_ticket.html', ticket=ticket)

@app.route('/flight-tickets/<int:id>/edit', methods=['GET', 'POST'])
def edit_flight_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = FlightTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    if request.method == 'POST':
        try:
            ticket.flight_number = request.form['flight_number']
            ticket.cabin_class = request.form['cabin_class']
            ticket.seat_number = request.form['seat_number']
            ticket.price = float(request.form['price'])
            ticket.airline = request.form['airline']
            ticket.airline_code = request.form['airline_code']
            ticket.departure_airport = request.form['departure_airport']
            ticket.departure_airport_code = request.form['departure_airport_code']
            ticket.departure_terminal = request.form['departure_terminal']
            ticket.boarding_gate = request.form['boarding_gate']
            ticket.arrival_airport = request.form['arrival_airport']
            ticket.arrival_airport_code = request.form['arrival_airport_code']
            ticket.scheduled_departure_date = datetime.strptime(request.form['scheduled_departure_date'], '%Y-%m-%d').date()
            ticket.scheduled_departure_time = datetime.strptime(request.form['scheduled_departure_time'], '%H:%M').time()
            ticket.scheduled_arrival_date = datetime.strptime(request.form['scheduled_arrival_date'], '%Y-%m-%d').date()
            ticket.scheduled_arrival_time = datetime.strptime(request.form['scheduled_arrival_time'], '%H:%M').time()
            ticket.departure_delay = request.form['departure_delay']
            ticket.arrival_delay = request.form['arrival_delay']
            ticket.aircraft_type = request.form['aircraft_type']
            ticket.registration_number = request.form['registration_number']
            ticket.has_baggage_check = request.form['has_baggage_check']
            ticket.departure_runway = request.form['departure_runway']
            ticket.arrival_runway = request.form['arrival_runway']
            ticket.etkt_number = request.form['etkt_number']
            ticket.remarks = request.form['remarks']
            ticket.distance = float(request.form['distance']) if request.form['distance'] else None
            
            if 'ticket_image' in request.files and request.files['ticket_image'].filename != '':
                ticket.set_ticket_image(request.files['ticket_image'])
            
            db.session.commit()
            flash('飞机票更新成功', 'success')
            return redirect(url_for('view_flight_ticket', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('tickets/edit_flight_ticket.html', ticket=ticket)

@app.route('/flight-tickets/<int:id>/delete', methods=['POST'])
def delete_flight_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    ticket = FlightTicket.query.get_or_404(id)
    if ticket.user_id != session['user_id']:
        abort(403)
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        flash('飞机票删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('flight_tickets'))


@app.route('/metrocard-tickets')
def metrocard_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cards = MetroCard.query.filter_by(user_id=session['user_id']).order_by(
        MetroCard.acquire_date.desc()
    ).all()
    return render_template('tickets/metrocard_tickets.html', cards=cards)

@app.route('/metrocard-tickets/add', methods=['GET', 'POST'])
def add_metrocard_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            card = MetroCard(
                user_id=session['user_id'],
                city=request.form['city'],
                card_type=request.form['card_type'],
                acquire_date=datetime.strptime(request.form['acquire_date'], '%Y-%m-%d').date(),
                acquire_method=request.form['acquire_method'],
                card_number=request.form['card_number'],
                edition=request.form['edition'],
                front_image=request.form['front_image'],
                back_image=request.form['back_image']
            )
            db.session.add(card)
            db.session.commit()
            flash('票卡添加成功', 'success')
            return redirect(url_for('metrocard_tickets'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')

    return render_template('tickets/add_metrocard_ticket.html')

@app.route('/metrocard-tickets/<int:id>')
def view_metrocard_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    card = MetroCard.query.get_or_404(id)
    if card.user_id != session['user_id']:
        abort(403)

    return render_template('tickets/view_metrocard_ticket.html', card=card)

@app.route('/metrocard-tickets/<int:id>/edit', methods=['GET', 'POST'])
def edit_metrocard_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    card = MetroCard.query.get_or_404(id)
    if card.user_id != session['user_id']:
        abort(403)

    if request.method == 'POST':
        try:
            card.city = request.form['city']
            card.card_type = request.form['card_type']
            card.acquire_date = datetime.strptime(request.form['acquire_date'], '%Y-%m-%d').date()
            card.acquire_method = request.form['acquire_method']
            card.card_number = request.form['card_number']
            card.edition = request.form['edition']
            card.front_image = request.form['front_image']
            card.back_image = request.form['back_image']
            db.session.commit()
            flash('票卡更新成功', 'success')
            return redirect(url_for('view_metrocard_ticket', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')

    return render_template('tickets/edit_metrocard_ticket.html', card=card)

@app.route('/metrocard-tickets/<int:id>/delete', methods=['POST'])
def delete_metrocard_ticket(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    card = MetroCard.query.get_or_404(id)
    if card.user_id != session['user_id']:
        abort(403)

    try:
        db.session.delete(card)
        db.session.commit()
        flash('票卡删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')

    return redirect(url_for('metrocard_tickets'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)