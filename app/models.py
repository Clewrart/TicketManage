from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import base64

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'usr'
    
    usrID = db.Column(db.Integer, primary_key=True, comment='人员编号')
    Phone = db.Column(db.String(12), unique=True, nullable=True, comment='登录手机号')
    Pwd = db.Column(db.String(255), nullable=True, comment='密码')
    UsrName = db.Column(db.String(30), nullable=True, comment='用户名')
    
    # 关系
    train_tickets = db.relationship('TrainTicket', backref='user', lazy=True)
    flight_tickets = db.relationship('FlightTicket', backref='user', lazy=True)
    
    def set_password(self, password):
        self.Pwd = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.Pwd, password)

class TrainTicket(db.Model):
    __tablename__ = 'trainticket'
    TrainRecordID      = db.Column(db.Integer, primary_key=True, comment='记录号(主键)')
    user_id            = db.Column(db.Integer, db.ForeignKey('usr.usrID'), nullable=False, comment='用户号(关联User表)')
    train_number       = db.Column(db.String(20), nullable=False, comment='车次(如G1234)')
    departure_date     = db.Column(db.Date, nullable=True, comment='出发日期')
    departure_time     = db.Column(db.Time, nullable=True, comment='出发时间')
    arrival_date       = db.Column(db.Date, nullable=True, comment='到达日期')
    arrival_time       = db.Column(db.Time, nullable=True, comment='到达时间')
    go_deltatime       = db.Column(db.String(50), nullable=True, comment='发车正晚点')
    arrive_deltatime   = db.Column(db.String(50), nullable=True, comment='到达正晚点')
    departure_station  = db.Column(db.String(50), nullable=True, comment='出发站')
    arrival_station    = db.Column(db.String(50), nullable=True, comment='终到站')
    ticket_class       = db.Column(db.String(50), nullable=True, comment='购票等级')
    seat_number        = db.Column(db.String(20), nullable=True,  comment='席位号(如12车05A号)')
    price              = db.Column(db.Numeric(10,2), nullable=True, comment='票价')
    distance           = db.Column(db.Numeric(10,3), nullable=True,  comment='里程数(公里)')
    railwaycom         = db.Column(db.String(50), nullable=True,  comment='执行路局')
    train_model        = db.Column(db.String(50), nullable=True,  comment='车型')
    train_code         = db.Column(db.String(50), nullable=True,  comment='车号')
    ticket_photo       = db.Column(db.Text,     nullable=True,  comment='车票照片(base64编码)')


class FlightTicket(db.Model):
    __tablename__ = 'flightticket'
    flightRecordID          = db.Column(db.Integer, primary_key=True, comment='记录号(主键)')
    user_id                 = db.Column(db.Integer, db.ForeignKey('usr.usrID'), nullable=False, comment='用户号(关联usr表usrID)')
    flight_number           = db.Column(db.String(20), nullable=False, comment='航班号')
    cabin_class             = db.Column(db.String(50), nullable=True, comment='舱位等级')
    seat_number             = db.Column(db.String(20), nullable=True,  comment='座位号')
    price                   = db.Column(db.Numeric(10,2), nullable=True, comment='支付票价')
    airline                 = db.Column(db.String(100),nullable=True, comment='航空公司')
    airline_code            = db.Column(db.String(10), nullable=True, comment='航司二字码')
    departure_airport       = db.Column(db.String(100),nullable=True, comment='始发机场')
    departure_airport_code  = db.Column(db.String(3), nullable=True, comment='始发机场三字码')
    departure_terminal      = db.Column(db.String(20), nullable=True,  comment='始发航站楼')
    boarding_gate           = db.Column(db.String(20), nullable=True,  comment='登机口')
    distance                = db.Column(db.Numeric(10,3), nullable=True,  comment='里程数(公里)')
    arrival_airport         = db.Column(db.String(100),nullable=True, comment='到达机场')
    arrival_airport_code    = db.Column(db.String(10), nullable=True, comment='到达机场三字码')
    scheduled_departure_date= db.Column(db.Date,    nullable=True, comment='计划起飞日期')
    scheduled_departure_time= db.Column(db.Time,    nullable=True, comment='计划起飞时间')
    scheduled_arrival_date  = db.Column(db.Date,    nullable=True, comment='计划到达日期')
    scheduled_arrival_time  = db.Column(db.Time,    nullable=True, comment='计划到达时间')
    departure_delay         = db.Column(db.String(255),nullable=True, comment='起飞正晚点情况')
    arrival_delay           = db.Column(db.String(255),nullable=True, comment='到达正晚点情况')
    aircraft_type           = db.Column(db.String(50), nullable=True,  comment='机型')
    registration_number     = db.Column(db.String(20), nullable=True,  comment='注册号')
    has_baggage_check       = db.Column(db.String(255),nullable=True, comment='行李托运状况')
    departure_runway        = db.Column(db.String(20), nullable=True,  comment='起飞跑道')
    arrival_runway          = db.Column(db.String(20), nullable=True,  comment='降落跑道')
    etkt_number             = db.Column(db.String(50), nullable=True,  unique=True, comment='ETKT票号')
    remarks                 = db.Column(db.Text,     nullable=True,  comment='其他事项记录')
    ticket_image            = db.Column(db.Text,     nullable=True,  comment='票据图片(base64)')

def set_ticket_image(self, image_file):
        if image_file:
            self.ticket_image = base64.b64encode(image_file.read()).decode('utf-8')