-- Redis IRIS Demo - Travel Database Schema
-- This schema will be synced to Redis via RDI

-- Destinations table
CREATE TABLE destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    best_season VARCHAR(50),
    description TEXT,
    average_temp_celsius INTEGER,
    popular_activities TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hotels table
CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    destination_id INTEGER REFERENCES destinations(id),
    address TEXT,
    price_range VARCHAR(20) CHECK (price_range IN ('budget', 'moderate', 'luxury', 'ultra-luxury')),
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
    amenities TEXT[],
    room_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activities table
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    destination_id INTEGER REFERENCES destinations(id),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) CHECK (category IN ('adventure', 'cultural', 'food', 'nature', 'shopping', 'nightlife')),
    description TEXT,
    duration_hours INTEGER,
    price_usd DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restaurants table
CREATE TABLE restaurants (
    id SERIAL PRIMARY KEY,
    destination_id INTEGER REFERENCES destinations(id),
    name VARCHAR(200) NOT NULL,
    cuisine_type VARCHAR(100),
    price_range VARCHAR(20) CHECK (price_range IN ('budget', 'moderate', 'fine-dining')),
    rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
    dietary_options TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Travel Preferences (for personalization)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL UNIQUE,
    preferred_destinations TEXT[],
    budget_level VARCHAR(20) CHECK (budget_level IN ('budget', 'moderate', 'luxury')),
    preferred_activities TEXT[],
    dietary_restrictions TEXT[],
    travel_style VARCHAR(50) CHECK (travel_style IN ('adventure', 'relaxation', 'cultural', 'mixed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_destinations_country ON destinations(country);
CREATE INDEX idx_hotels_destination ON hotels(destination_id);
CREATE INDEX idx_hotels_price_range ON hotels(price_range);
CREATE INDEX idx_hotels_rating ON hotels(rating);
CREATE INDEX idx_activities_destination ON activities(destination_id);
CREATE INDEX idx_activities_category ON activities(category);
CREATE INDEX idx_restaurants_destination ON restaurants(destination_id);
CREATE INDEX idx_restaurants_cuisine ON restaurants(cuisine_type);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_destinations_updated_at BEFORE UPDATE ON destinations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_hotels_updated_at BEFORE UPDATE ON hotels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON activities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
