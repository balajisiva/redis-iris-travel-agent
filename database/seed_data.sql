-- Sample data for Redis IRIS Travel Demo

-- Destinations
INSERT INTO destinations (name, country, region, best_season, description, average_temp_celsius, popular_activities) VALUES
('Paris', 'France', 'Île-de-France', 'April-June, September-October', 'The City of Light, famous for art, fashion, and cuisine', 15, ARRAY['museums', 'dining', 'architecture', 'shopping']),
('Tokyo', 'Japan', 'Kanto', 'March-May, September-November', 'A blend of traditional and modern culture', 16, ARRAY['temples', 'shopping', 'dining', 'technology']),
('Barcelona', 'Spain', 'Catalonia', 'May-June, September-October', 'Mediterranean coast with Gaudí architecture', 18, ARRAY['beaches', 'architecture', 'nightlife', 'museums']),
('Bali', 'Indonesia', 'Bali Province', 'April-October', 'Tropical paradise with temples and beaches', 27, ARRAY['beaches', 'surfing', 'temples', 'yoga']),
('New York City', 'USA', 'New York', 'April-June, September-November', 'The city that never sleeps', 13, ARRAY['museums', 'broadway', 'dining', 'shopping']),
('Rome', 'Italy', 'Lazio', 'April-June, September-October', 'Ancient history meets modern Italian culture', 17, ARRAY['history', 'museums', 'dining', 'architecture']),
('Iceland', 'Iceland', 'N/A', 'June-August', 'Land of fire and ice with stunning natural beauty', 10, ARRAY['hiking', 'northern-lights', 'hot-springs', 'glaciers']),
('Lisbon', 'Portugal', 'Lisbon District', 'March-May, September-October', 'Coastal charm with historic neighborhoods', 17, ARRAY['history', 'beaches', 'dining', 'nightlife']);

-- Hotels
INSERT INTO hotels (name, destination_id, address, price_range, rating, amenities, room_count) VALUES
-- Paris hotels
('Hotel Le Meurice', 1, '228 Rue de Rivoli, 75001 Paris', 'luxury', 4.8, ARRAY['spa', 'restaurant', 'concierge', 'gym'], 160),
('Ibis Budget Paris', 1, '15 Rue de la Tour, 75016 Paris', 'budget', 3.5, ARRAY['wifi', 'breakfast'], 200),
-- Tokyo hotels
('The Ritz-Carlton Tokyo', 2, 'Tokyo Midtown, 9-7-1 Akasaka', 'ultra-luxury', 4.9, ARRAY['spa', 'michelin-restaurant', 'pool', 'gym'], 245),
('Hotel Gracery Shinjuku', 2, '1-19-1 Kabukicho, Shinjuku', 'moderate', 4.0, ARRAY['restaurant', 'wifi', 'godzilla-view'], 970),
-- Barcelona hotels
('Hotel Arts Barcelona', 3, 'Marina 19-21, 08005 Barcelona', 'luxury', 4.7, ARRAY['beach', 'spa', 'pool', 'restaurants'], 483),
('Generator Barcelona', 3, 'Carrer de Còrsega, 373', 'budget', 3.8, ARRAY['bar', 'wifi', 'social-spaces'], 245),
-- Bali hotels
('Four Seasons Resort Bali', 4, 'Jalan Goa Lempeh, Banjar Dinas Kangin', 'ultra-luxury', 4.9, ARRAY['beach', 'spa', 'villas', 'infinity-pool'], 147),
('Kuta Beach Hostel', 4, 'Jl. Pantai Kuta No.9', 'budget', 3.6, ARRAY['beach-access', 'wifi', 'surfboard-rental'], 60);

-- Activities
INSERT INTO activities (destination_id, name, category, description, duration_hours, price_usd) VALUES
(1, 'Louvre Museum Tour', 'cultural', 'Explore the world''s largest art museum', 3, 45.00),
(1, 'Seine River Dinner Cruise', 'food', 'Romantic dinner cruise with Eiffel Tower views', 2, 125.00),
(1, 'Montmartre Walking Tour', 'cultural', 'Discover the artistic heart of Paris', 3, 35.00),
(2, 'Tokyo Fish Market Tour', 'food', 'Early morning sushi and seafood experience', 4, 80.00),
(2, 'Mt. Fuji Day Trip', 'nature', 'Visit Japan''s iconic mountain', 10, 150.00),
(3, 'Sagrada Familia Tour', 'cultural', 'Gaudí''s masterpiece basilica', 2, 40.00),
(3, 'Barcelona Beach Day', 'nature', 'Relax at Barceloneta Beach', 4, 0.00),
(4, 'Ubud Rice Terrace Trek', 'nature', 'Hike through stunning rice paddies', 4, 35.00),
(4, 'Surf Lesson at Kuta', 'adventure', 'Learn to surf at famous Kuta Beach', 2, 50.00);

-- Restaurants
INSERT INTO restaurants (destination_id, name, cuisine_type, price_range, rating, dietary_options) VALUES
(1, 'Le Jules Verne', 'French Fine Dining', 'fine-dining', 4.7, ARRAY['vegetarian-options']),
(1, 'L''As du Fallafel', 'Middle Eastern', 'budget', 4.5, ARRAY['vegetarian', 'vegan']),
(1, 'Bouillon Chartier', 'Traditional French', 'moderate', 4.0, ARRAY['vegetarian-options']),
(2, 'Sukiyabashi Jiro', 'Sushi', 'fine-dining', 4.9, ARRAY['seafood-only']),
(2, 'Ichiran Ramen', 'Ramen', 'budget', 4.3, ARRAY['vegetarian-options']),
(3, 'Tickets Bar', 'Spanish Tapas', 'fine-dining', 4.8, ARRAY['vegetarian', 'gluten-free']),
(3, 'La Boqueria Market', 'Market Food', 'budget', 4.6, ARRAY['vegetarian', 'vegan', 'all-options']),
(4, 'Locavore', 'Modern Indonesian', 'fine-dining', 4.8, ARRAY['vegetarian', 'vegan']),
(4, 'Warung Biah Biah', 'Traditional Balinese', 'budget', 4.4, ARRAY['vegetarian-options']);

-- Sample user preferences
INSERT INTO user_preferences (user_id, preferred_destinations, budget_level, preferred_activities, dietary_restrictions, travel_style) VALUES
('alice', ARRAY['Paris', 'Rome'], 'moderate', ARRAY['museums', 'dining', 'architecture'], ARRAY[]::text[], 'cultural'),
('bob', ARRAY['Tokyo', 'Bali'], 'luxury', ARRAY['food', 'beaches', 'spas'], ARRAY['vegetarian'], 'relaxation');
