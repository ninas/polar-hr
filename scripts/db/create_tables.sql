CREATE TYPE SPORT AS ENUM (
  'HIIT',
  'Strength',
  'Core',
  'Circuit Training',
  'Unknown'
);

CREATE TYPE EQUIPMENT_TYPE as ENUM (
  'Weights',
  'Band'
);

CREATE TYPE SOURCE_TYPE as ENUM (
  'Youtube'
);

CREATE TYPE HR_ZONE as (
  lowerLimit INTEGER,
  higherLimit INTEGER,
  duration INTERVAL
);

CREATE TABLE IF NOT EXISTS equipment (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  equipmentType EQUIPMENT_TYPE NOT NULL,
  magnitude TEXT NOT NULL,
  quantity INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  url TEXT NOT NULL UNIQUE,
  sourceType SOURCE_TYPE,
  name TEXT,
  length INTERVAL,
  notes TEXT,
  extraInfo JSON
);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name TEXT NOT NULL,
  sourceID INTEGER NOT NULL,
  CONSTRAINT fk_sourceID
    FOREIGN KEY(sourceID)
      REFERENCES sources(id)
      ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS workout (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  startTime TIMESTAMP WITH TIME ZONE NOT NULL,
  endTime TIMESTAMP WITH TIME ZONE NOT NULL,
  sport SPORT DEFAULT 'Unknown',
  maxHR INTEGER,
  minHR INTEGER,
  avgHR INTEGER,
  calories INTEGER,
  hrZones HR_ZONE[5],
  fitFat HR_ZONE[2],
  samples JSON NOT NULL,
  notes TEXT,
  sourceID INTEGER,
  equipmentID INTEGER,
  CONSTRAINT fk_sourceID
    FOREIGN KEY(sourceID)
      REFERENCES sources(id)
      ON DELETE NO ACTION,
  CONSTRAINT fk_equpmentID
    FOREIGN KEY(equipmentID)
      REFERENCES equipment(id)
      ON DELETE NO ACTION
);
