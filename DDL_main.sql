--users table

CREATE TABLE aiti_guru_api.users(
id serial PRIMARY KEY,
name varchar NOT NULL,
current_money float NOT null
)
ALTER TABLE aiti_guru_api.users ADD CONSTRAINT current_money_ge_0 CHECK (current_money >= 0)


------------------------------------------------------------------------------------------------------
--orders table

CREATE TABLE aiti_guru_api.orders(
id serial PRIMARY KEY,
user_id int NOT NULL REFERENCES aiti_guru_api.users(id),
item_name varchar,
cost float NOT null,
remained_cost float NOT NULL,
status varchar NOT NULL,
created_at timestamp DEFAULT now()
CONSTRAINT remained_cost_no_more_than_cost CHECK (remained_cost <= cost)
)
ALTER TABLE aiti_guru_api.orders ADD CONSTRAINT status_set CHECK (status IN ('Не оплачен', 'Частично оплачен', 'Оплачен'));
ALTER TABLE aiti_guru_api.orders ADD CONSTRAINT remained_cost_ge_0 CHECK (remained_cost >= 0)

CREATE OR REPLACE FUNCTION set_default_order_values()
RETURNS TRIGGER AS $$
BEGIN
    NEW.remained_cost := NEW.cost;
	NEW.status := 'Не оплачен';
    NEW.created_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_default_order_values
BEFORE INSERT ON aiti_guru_api.orders
FOR EACH ROW
EXECUTE FUNCTION set_default_order_values();


----------------------------------------------------------------------------------------
--payments table

CREATE TABLE aiti_guru_api.payments(
id serial PRIMARY KEY,
order_id int NOT NULL REFERENCES aiti_guru_api.orders(id),
amount float NOT null, 
type varchar,
created_at timestamp DEFAULT now()
)
ALTER TABLE aiti_guru_api.payments ADD CONSTRAINT type_set CHECK (type IN (NULL, 'Наличные', 'Эквайринг'))


CREATE OR REPLACE FUNCTION validating_payment_and_set_created_at()
RETURNS TRIGGER AS $$
DECLARE 
	f_remained_cost FLOAT;
	f_user_id INT;
	f_current_money FLOAT;
BEGIN
	SELECT o.remained_cost INTO f_remained_cost FROM aiti_guru_api.orders o WHERE id = NEW.order_id;
	IF f_remained_cost < NEW.amount THEN
		RAISE NOTICE 'Отмена вставки, так как remained_cost (%) < amount (%)', f_remained_cost, NEW.amount;
		RETURN NULL;
	END IF;
	
	SELECT o.user_id INTO f_user_id FROM aiti_guru_api.orders o WHERE id = NEW.order_id;
	SELECT current_money INTO f_current_money FROM aiti_guru_api.users WHERE id = f_user_id;

	IF f_current_money < NEW.amount THEN
		RAISE NOTICE 'Отмена вставки, так как current_money (%) < amount (%)', f_current_money, NEW.amount;
		RETURN NULL;
	END IF;

	UPDATE aiti_guru_api.orders o SET remained_cost = remained_cost - NEW.amount WHERE o.id = NEW.order_id;
	UPDATE aiti_guru_api.users u SET current_money = current_money - NEW.amount WHERE u.id = f_user_id;
	
	NEW.created_at := NOW()::timestamp;
    RETURN NEW; 
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validating_payment_and_set_created_at
BEFORE INSERT ON aiti_guru_api.payments
FOR EACH ROW
EXECUTE FUNCTION validating_payment_and_set_created_at();



CREATE OR REPLACE FUNCTION status_correcting()
RETURNS TRIGGER AS $$
BEGIN
	IF NEW.remained_cost = 0.0 THEN 
		NEW.status := 'Оплачен';
		RETURN NEW;
	END IF;
	
	IF (NEW.remained_cost > 0.0) AND (NEW.remained_cost < NEW."cost") THEN 
		NEW.status := 'Частично оплачен';
		RETURN NEW;
	END IF;

	IF (NEW.remained_cost = NEW."cost") THEN
		NEW.status := 'Не оплачен';
		RETURN NEW;
	END IF;

END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER status_correcting
BEFORE UPDATE ON aiti_guru_api.orders
FOR EACH ROW
EXECUTE FUNCTION status_correcting();




CREATE OR REPLACE FUNCTION remained_cost_and_current_money_correcting()
RETURNS TRIGGER AS $$
DECLARE 
	f_user_id INT;
BEGIN
	SELECT o.user_id INTO f_user_id FROM aiti_guru_api.orders o WHERE id = OLD.order_id;
	UPDATE aiti_guru_api.orders o SET remained_cost = remained_cost + OLD.amount WHERE o.id = OLD.order_id;
	UPDATE aiti_guru_api.users u SET current_money = current_money + OLD.amount WHERE u.id = f_user_id;
	RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER remained_cost_and_current_money_correcting
BEFORE DELETE ON aiti_guru_api.payments
FOR EACH ROW
EXECUTE FUNCTION remained_cost_and_current_money_correcting();
