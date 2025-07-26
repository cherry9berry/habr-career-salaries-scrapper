-- Специализации
INSERT INTO specializations (title, alias) VALUES
('Backend Developer', 'backend'),
('Frontend Developer', 'frontend'),
('DevOps Engineer', 'devops'),
('Data Scientist', 'data-science'),
('QA Engineer', 'qa'),
('Android Developer', 'android'),
('iOS Developer', 'ios'),
('Full Stack Developer', 'fullstack')
ON CONFLICT (alias) DO NOTHING;

-- Навыки
INSERT INTO skills (title, alias) VALUES
('Python', 'python'),
('JavaScript', 'javascript'),
('Java', 'java'),
('C++', 'cpp'),
('Go', 'golang'),
('React', 'react'),
('Vue.js', 'vue'),
('Angular', 'angular'),
('Docker', 'docker'),
('Kubernetes', 'kubernetes'),
('PostgreSQL', 'postgresql'),
('MongoDB', 'mongodb'),
('Git', 'git'),
('Linux', 'linux'),
('AWS', 'aws'),
('SQL', 'sql')
ON CONFLICT (alias) DO NOTHING;

-- Регионы
INSERT INTO regions (title, alias) VALUES
('Москва', 'moscow'),
('Санкт-Петербург', 'spb'),
('Новосибирск', 'novosibirsk'),
('Екатеринбург', 'ekaterinburg'),
('Казань', 'kazan'),
('Нижний Новгород', 'nn'),
('Удаленная работа', 'remote')
ON CONFLICT (alias) DO NOTHING;

-- Компании
INSERT INTO companies (title, alias) VALUES
('Яндекс', 'yandex'),
('VK', 'vk'),
('Сбер', 'sber'),
('Тинькофф', 'tinkoff'),
('Ozon', 'ozon'),
('Avito', 'avito'),
('Wildberries', 'wildberries'),
('HeadHunter', 'hh')
ON CONFLICT (alias) DO NOTHING; 