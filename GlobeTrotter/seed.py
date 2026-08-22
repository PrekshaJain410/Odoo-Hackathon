from app import create_app, db
from app.models import User, City, Activity
from werkzeug.security import generate_password_hash

app = create_app()

cities = [
("Paris","France","Europe",78,98,"https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=900&q=80","Cafés, art, architecture and iconic city walks."),
("Rome","Italy","Europe",70,96,"https://images.unsplash.com/photo-1529260830199-42c24126f198?auto=format&fit=crop&w=900&q=80","Ancient history, food and unforgettable streets."),
("Tokyo","Japan","Asia",82,97,"https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=900&q=80","Neon neighborhoods, temples and world-class food."),
("Bali","Indonesia","Asia",48,93,"https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=900&q=80","Beaches, rice terraces, wellness and adventure."),
("Dubai","UAE","Middle East",88,91,"https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=900&q=80","Skylines, desert experiences and luxury escapes."),
("New York","USA","North America",92,95,"https://images.unsplash.com/photo-1496588152823-86ff7695e68f?auto=format&fit=crop&w=900&q=80","Museums, neighborhoods, food and city energy."),
("Barcelona","Spain","Europe",76,94,"https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=900&q=80","Gaudí architecture, beaches and tapas."),
("Sydney","Australia","Oceania",86,89,"https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d5?auto=format&fit=crop&w=900&q=80","Harbour views, beaches and coastal adventures.")
]

activities = {
"Paris":[("Eiffel Tower Sunset","Sightseeing","Watch the city glow from the Eiffel Tower.",2,35),("Louvre Highlights","Culture","A guided route through the museum's classics.",3,28),("Seine Dinner Cruise","Food","Evening cruise with city views.",2.5,65)],
"Rome":[("Colosseum Tour","History","Explore the ancient amphitheatre with a guide.",2.5,40),("Trastevere Food Walk","Food","Taste local specialties through a lively neighborhood.",3,55),("Vatican Museums","Culture","See the Vatican collections and Sistine Chapel.",3,45)],
"Tokyo":[("Shibuya Night Walk","City","Explore neon streets and hidden lanes.",2,20),("Sushi Workshop","Food","Learn sushi techniques from a local chef.",2.5,60),("Meiji Shrine","Culture","A calm escape in the heart of the city.",1.5,0)],
"Bali":[("Ubud Rice Terraces","Nature","Scenic walk through iconic terraces.",3,15),("Sunrise Mount Batur","Adventure","Early-morning trek with sunrise views.",6,45),("Balinese Cooking Class","Food","Cook traditional dishes with local ingredients.",3,35)],
"Dubai":[("Desert Safari","Adventure","Dune drive, sunset and camp experience.",6,75),("Burj Khalifa","Sightseeing","Skyline views from the world's famous tower.",2,50),("Old Dubai Walk","Culture","Explore souks and historic neighborhoods.",2,10)],
"New York":[("Central Park Walk","Nature","Explore iconic paths, bridges and viewpoints.",2,0),("Broadway Show","Entertainment","Experience a live theatre performance.",3,100),("Brooklyn Food Tour","Food","Taste neighborhood favorites.",3,65)],
"Barcelona":[("Sagrada Família","Culture","Discover Gaudí's masterpiece.",2,30),("Gothic Quarter Walk","History","Walk through medieval streets and plazas.",2,10),("Tapas Evening","Food","Sample tapas and local drinks.",2.5,50)],
"Sydney":[("Harbour Bridge Walk","Sightseeing","See the harbour from an iconic viewpoint.",2,25),("Bondi to Coogee Walk","Nature","Coastal trail with ocean views.",3,0),("Opera House Tour","Culture","Explore the architecture and history.",1.5,30)]
}

with app.app_context():
    db.create_all()
    for name,country,region,cost,pop,img,desc in cities:
        city = City.query.filter_by(name=name,country=country).first()
        if not city:
            city = City(name=name,country=country,region=region,cost_index=cost,popularity=pop,image_url=img,description=desc)
            db.session.add(city)
            db.session.flush()
        for aname,cat,adesc,duration,price in activities.get(name,[]):
            if not Activity.query.filter_by(city_id=city.id,name=aname).first():
                db.session.add(Activity(city_id=city.id,name=aname,category=cat,description=adesc,duration_hours=duration,estimated_cost=price,image_url=img))
    admin = User.query.filter_by(email="admin@globetrotter.local").first()
    if not admin:
        admin = User(name="GlobeTrotter Admin",email="admin@globetrotter.local",password_hash=generate_password_hash("Admin@12345",method="scrypt"),is_admin=True)
        db.session.add(admin)
    db.session.commit()
    print("Seed complete. Cities, activities and demo admin are ready.")
    print("Demo admin: admin@globetrotter.local / Admin@12345")