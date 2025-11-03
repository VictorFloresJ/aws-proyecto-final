Write-Host "=== CREANDO ALUMNOS ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":1,"nombres":"Juan","apellidos":"Pérez","matricula":"A123","promedio":9.5}'
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":2,"nombres":"María","apellidos":"López","matricula":"B456","promedio":8.7}'

Write-Host "=== LISTANDO ALUMNOS ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos" -Method GET | ConvertTo-Json -Depth 5

Write-Host "=== GET ALUMNO POR ID ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos/1" -Method GET | ConvertTo-Json -Depth 5

Write-Host "=== ACTUALIZANDO ALUMNO ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos/1" -Method PUT -Headers @{ "Content-Type" = "application/json" } -Body '{"promedio":10.0}'

Write-Host "=== ELIMINANDO ALUMNO ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos/2" -Method DELETE

Write-Host "=== CREANDO PROFESORES ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":1,"numeroEmpleado":"EMP001","nombres":"Ana","apellidos":"Martínez","horasClase":20}'
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":2,"numeroEmpleado":"EMP002","nombres":"Luis","apellidos":"Gómez","horasClase":15}'

Write-Host "=== LISTANDO PROFESORES ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores" -Method GET | ConvertTo-Json -Depth 5

Write-Host "=== GET PROFESOR POR ID ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores/1" -Method GET | ConvertTo-Json -Depth 5

Write-Host "=== ACTUALIZANDO PROFESOR ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores/2" -Method PUT -Headers @{ "Content-Type" = "application/json" } -Body '{"horasClase":18}'

Write-Host "=== ELIMINANDO PROFESOR ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores/1" -Method DELETE

# ---------------- ERRORES ----------------
Write-Host "=== ERROR: CAMPOS INCOMPLETOS (Alumno) ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":99,"nombres":"Error","apellidos":"Prueba","promedio":9.0}'

Write-Host "=== ERROR: TIPO INCORRECTO (Profesor) ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":99,"numeroEmpleado":"EMP099","nombres":"Error","apellidos":"Tipo","horasClase":"veinte"}'

Write-Host "=== ERROR: ID DUPLICADO (Alumno) ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{"id":1,"nombres":"Duplicado","apellidos":"Alumno","matricula":"Z999","promedio":6.0}'

Write-Host "=== ERROR: NO ENCONTRADO (Profesor GET) ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/profesores/999" -Method GET

Write-Host "=== ERROR: NO ENCONTRADO (Alumno DELETE) ==="
Invoke-RestMethod -Uri "http://127.0.0.1:5000/alumnos/999" -Method DELETE