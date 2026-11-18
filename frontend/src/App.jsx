// Tabla de rutas del sistema. Todo, menos el login, pide sesión
// y se muestra dentro del layout con la barra lateral.
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import RutaProtegida from './components/RutaProtegida.jsx'
import Citas from './pages/Citas.jsx'
import Clientes from './pages/Clientes.jsx'
import DetalleCita from './pages/DetalleCita.jsx'
import FormularioCita from './pages/FormularioCita.jsx'
import FormularioCliente from './pages/FormularioCliente.jsx'
import FormularioRefaccion from './pages/FormularioRefaccion.jsx'
import FormularioVehiculo from './pages/FormularioVehiculo.jsx'
import HistorialVehiculo from './pages/HistorialVehiculo.jsx'
import Inventario from './pages/Inventario.jsx'
import Login from './pages/Login.jsx'
import Proximamente from './pages/Proximamente.jsx'
import Vehiculos from './pages/Vehiculos.jsx'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* RN-13: solo el administrador con sesión entra a estas rutas */}
      <Route
        element={
          <RutaProtegida>
            <Layout />
          </RutaProtegida>
        }
      >
        <Route path="/" element={<Navigate to="/inventario" replace />} />
        <Route path="/inventario" element={<Inventario />} />
        <Route path="/inventario/nueva" element={<FormularioRefaccion />} />
        <Route path="/inventario/:id_pieza/editar" element={<FormularioRefaccion />} />
        <Route path="/resumen" element={<Proximamente titulo="Resumen" />} />

        {/* Las rutas fijas (/nuevo, /nueva) van antes de las que llevan :id */}
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/clientes/nuevo" element={<FormularioCliente />} />
        <Route path="/clientes/:id_cliente/editar" element={<FormularioCliente />} />

        <Route path="/vehiculos" element={<Vehiculos />} />
        <Route path="/vehiculos/nuevo" element={<FormularioVehiculo />} />
        <Route path="/vehiculos/:id_vehiculo/editar" element={<FormularioVehiculo />} />
        <Route path="/vehiculos/:id_vehiculo/historial" element={<HistorialVehiculo />} />

        <Route path="/citas" element={<Citas />} />
        <Route path="/citas/nueva" element={<FormularioCita />} />
        <Route path="/citas/:id_cita" element={<DetalleCita />} />
        <Route path="/citas/:id_cita/editar" element={<FormularioCita />} />
      </Route>

      <Route path="*" element={<Navigate to="/inventario" replace />} />
    </Routes>
  )
}

export default App
