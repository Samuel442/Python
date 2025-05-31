USE DB_Vendas_Informatica;
GO


INSERT INTO Vendas (data, produto, valor)
VALUES
('2025-01-10', 'Teclado', 150.00),
('2025-01-15', 'Mouse', 100.00),
('2025-02-01', 'Monitor', 850.00),
('2025-02-15', 'Notebook', 3500.00),
('2025-03-10', 'Cadeira Gamer', 1200.00),
('2025-03-15', 'Webcam', 300.00),
('2025-03-20', 'Headset', 250.00),
('2025-04-01', 'Impressora', 980.00),
('2025-04-05', 'HD Externo', 420.00),
('2025-04-10', 'Pen Drive', 80.00),
('2025-04-15', 'Monitor Curvo', 1350.00),
('2025-05-01', 'Placa de Vídeo', 2800.00),
('2025-05-03', 'Fonte 650W', 390.00),
('2025-05-05', 'SSD 1TB', 620.00),
('2025-05-10', 'Memória RAM 16GB', 430.00),
('2025-05-12', 'Gabinete Gamer', 540.00),
('2025-05-15', 'Mousepad RGB', 120.00),
('2025-05-20', 'Roteador', 210.00),
('2025-05-25', 'Switch 8 Portas', 310.00),
('2025-05-28', 'Teclado Mecânico', 280.00);
GO

SELECT * FROM Vendas;