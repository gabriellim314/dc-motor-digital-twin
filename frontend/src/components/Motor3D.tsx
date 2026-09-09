import { ContactShadows, OrbitControls } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { DoubleSide, type Group, type Mesh } from 'three'

export type MotorVisualStatus = 'normal' | 'warning' | 'error'

type Motor3DProps = {
  rpm: number
  status?: MotorVisualStatus
}

const STATUS_THEME: Record<
  MotorVisualStatus,
  { label: string; hex: string; badge: string }
> = {
  normal: {
    label: 'Normal',
    hex: '#34d399',
    badge: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300',
  },
  warning: {
    label: 'Warning',
    hex: '#fbbf24',
    badge: 'border-amber-400/40 bg-amber-400/15 text-amber-300',
  },
  error: {
    label: 'Error',
    hex: '#f87171',
    badge: 'border-rose-400/40 bg-rose-500/15 text-rose-300',
  },
}

const RPM_TO_RAD_PER_SEC = (Math.PI * 2) / 60
const STOPPED_RPM = 1e-3

const PAINT = {
  housing: '#c5d0de',
  fins: '#8b9bb0',
  endBell: '#a8b6c8',
  bearing: '#d7dee8',
  cowl: '#9aa8ba',
  terminal: '#b4c0d0',
  plate: '#6f7f93',
  base: '#7d8b9d',
  foot: '#5c6b7d',
  saddle: '#90a0b4',
  shaft: '#f3f6fa',
  coupling: '#e2e8f0',
  rotor: '#d97706',
  lamination: '#b45309',
  fan: '#cbd5e1',
  vent: '#4b5a6d',
}

function HousingFins() {
  const fins = useMemo(() => {
    const items: { y: number; z: number; rotation: [number, number, number] }[] = []
    for (let i = 0; i < 14; i += 1) {
      const angle = (i / 14) * Math.PI * 2
      const y = Math.sin(angle) * 0.56
      const z = Math.cos(angle) * 0.56
      if (y < -0.42) continue
      items.push({ y, z, rotation: [angle, 0, 0] })
    }
    return items
  }, [])

  return (
    <>
      {fins.map((fin) => (
        <mesh key={`${fin.y}-${fin.z}`} position={[0, fin.y, fin.z]} rotation={fin.rotation}>
          <boxGeometry args={[1.28, 0.07, 0.035]} />
          <meshStandardMaterial color={PAINT.fins} metalness={0.18} roughness={0.42} />
        </mesh>
      ))}
    </>
  )
}

function VentilationSlots() {
  const slots = useMemo(() => {
    return Array.from({ length: 10 }, (_, i) => {
      const angle = (i / 10) * Math.PI * 2
      return {
        position: [0.02, Math.sin(angle) * 0.36, Math.cos(angle) * 0.36] as [
          number,
          number,
          number,
        ],
        rotation: [angle, 0, 0] as [number, number, number],
      }
    })
  }, [])

  return (
    <group position={[-0.92, 0, 0]}>
      {slots.map((slot) => (
        <mesh key={slot.position.join(',')} position={slot.position} rotation={slot.rotation}>
          <boxGeometry args={[0.08, 0.16, 0.04]} />
          <meshStandardMaterial color={PAINT.vent} metalness={0.1} roughness={0.7} />
        </mesh>
      ))}
    </group>
  )
}

function MotorBase() {
  return (
    <group>
      <mesh position={[0, 0.08, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.7, 0.16, 0.95]} />
        <meshStandardMaterial color={PAINT.base} metalness={0.12} roughness={0.58} />
      </mesh>
      {[
        [-0.62, -0.34],
        [0.62, -0.34],
        [-0.62, 0.34],
        [0.62, 0.34],
      ].map(([x, z]) => (
        <mesh key={`${x}-${z}`} position={[x, 0.03, z]} castShadow>
          <boxGeometry args={[0.32, 0.06, 0.22]} />
          <meshStandardMaterial color={PAINT.foot} metalness={0.12} roughness={0.55} />
        </mesh>
      ))}
      <mesh position={[0, 0.22, 0]}>
        <boxGeometry args={[0.95, 0.14, 0.42]} />
        <meshStandardMaterial color={PAINT.saddle} metalness={0.14} roughness={0.5} />
      </mesh>
    </group>
  )
}

function StatusLamp({ color }: { color: string }) {
  const lamp = useRef<Mesh>(null)

  useFrame(({ clock }) => {
    if (!lamp.current) return
    const pulse = 0.45 + Math.sin(clock.elapsedTime * 3.2) * 0.25
    lamp.current.scale.setScalar(1 + pulse * 0.08)
    const material = lamp.current.material
    if ('emissiveIntensity' in material) {
      material.emissiveIntensity = 1.1 + pulse
    }
  })

  return (
    <mesh ref={lamp} position={[0.12, 0.16, 0.2]}>
      <sphereGeometry args={[0.045, 16, 16]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.4} />
    </mesh>
  )
}

function RotorAssembly({ rpm }: { rpm: number }) {
  const rotor = useRef<Group>(null)

  useFrame((_, delta) => {
    if (!rotor.current || Math.abs(rpm) < STOPPED_RPM) return
    rotor.current.rotation.x -= rpm * RPM_TO_RAD_PER_SEC * delta
  })

  const blades = useMemo(
    () =>
      Array.from({ length: 6 }, (_, i) => {
        const angle = (i / 6) * Math.PI * 2
        return { angle, key: i }
      }),
    [],
  )

  return (
    <group ref={rotor}>
      <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.07, 0.07, 2.55, 24]} />
        <meshStandardMaterial color={PAINT.shaft} metalness={0.55} roughness={0.18} />
      </mesh>
      <mesh position={[1.18, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.085, 0.085, 0.18, 24]} />
        <meshStandardMaterial color={PAINT.shaft} metalness={0.5} roughness={0.2} />
      </mesh>
      <mesh position={[1.32, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.16, 0.16, 0.08, 28]} />
        <meshStandardMaterial color={PAINT.coupling} metalness={0.35} roughness={0.28} />
      </mesh>
      <mesh position={[1.365, 0.07, 0]}>
        <boxGeometry args={[0.02, 0.09, 0.05]} />
        <meshStandardMaterial color="#22d3ee" metalness={0.2} roughness={0.35} />
      </mesh>
      <mesh position={[0, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.34, 0.34, 1.05, 32]} />
        <meshStandardMaterial color={PAINT.rotor} metalness={0.25} roughness={0.4} />
      </mesh>
      {[-0.38, -0.19, 0, 0.19, 0.38].map((x) => (
        <mesh key={x} position={[x, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.36, 0.36, 0.06, 32]} />
          <meshStandardMaterial color={PAINT.lamination} metalness={0.2} roughness={0.48} />
        </mesh>
      ))}
      <group position={[-1.08, 0, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.12, 0.12, 0.06, 20]} />
          <meshStandardMaterial color={PAINT.fan} metalness={0.3} roughness={0.3} />
        </mesh>
        {blades.map((blade) => (
          <group key={blade.key} rotation={[blade.angle, 0, 0]}>
            <mesh position={[0, 0.22, 0]}>
              <boxGeometry args={[0.03, 0.28, 0.08]} />
              <meshStandardMaterial color={PAINT.fan} metalness={0.22} roughness={0.35} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  )
}

function IndustrialMotor({ rpm, statusColor }: { rpm: number; statusColor: string }) {
  return (
    <group position={[0, 0.02, 0]}>
      <MotorBase />
      <group position={[0, 0.78, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.52, 0.52, 1.55, 48]} />
          <meshStandardMaterial color={PAINT.housing} metalness={0.16} roughness={0.38} />
        </mesh>
        <HousingFins />
        <mesh position={[0.86, 0, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.48, 0.5, 0.22, 40]} />
          <meshStandardMaterial color={PAINT.endBell} metalness={0.18} roughness={0.36} />
        </mesh>
        <mesh position={[-0.86, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.5, 0.48, 0.22, 40]} />
          <meshStandardMaterial color={PAINT.endBell} metalness={0.18} roughness={0.36} />
        </mesh>
        <mesh position={[1.02, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.22, 0.26, 0.16, 28]} />
          <meshStandardMaterial color={PAINT.bearing} metalness={0.28} roughness={0.32} />
        </mesh>
        <mesh position={[-1.04, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
          <ringGeometry args={[0.22, 0.46, 36]} />
          <meshStandardMaterial color={PAINT.cowl} metalness={0.16} roughness={0.42} side={DoubleSide} />
        </mesh>
        <VentilationSlots />
        <mesh position={[0.05, 0.52, 0]} castShadow>
          <boxGeometry args={[0.42, 0.28, 0.36]} />
          <meshStandardMaterial color={PAINT.terminal} metalness={0.14} roughness={0.48} />
        </mesh>
        <StatusLamp color={statusColor} />
        <mesh position={[0.02, 0.08, 0.525]} rotation={[Math.PI / 2, 0, 0]}>
          <boxGeometry args={[0.55, 0.02, 0.22]} />
          <meshStandardMaterial color={PAINT.plate} metalness={0.12} roughness={0.5} />
        </mesh>
        <RotorAssembly rpm={rpm} />
      </group>
    </group>
  )
}

function MotorScene({ rpm, statusColor }: { rpm: number; statusColor: string }) {
  return (
    <>
      <color attach="background" args={['#1e293b']} />
      <hemisphereLight args={['#e2e8f0', '#475569', 1.15]} />
      <ambientLight intensity={0.85} />
      <directionalLight position={[3.2, 5.2, 2.8]} intensity={2.1} castShadow />
      <directionalLight position={[-3.6, 2.4, -2.4]} intensity={0.95} color="#bae6fd" />
      <directionalLight position={[0.2, 1.8, 4.2]} intensity={0.7} color="#f8fafc" />
      <IndustrialMotor rpm={rpm} statusColor={statusColor} />
      <ContactShadows position={[0, 0, 0]} opacity={0.28} scale={6} blur={2.4} far={2} />
      <OrbitControls
        enablePan={false}
        minDistance={2.4}
        maxDistance={6}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, 0.55, 0]}
      />
    </>
  )
}

export function Motor3D({ rpm, status = 'normal' }: Motor3DProps) {
  const theme = STATUS_THEME[status]

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="flex items-center justify-between px-4 pt-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
          Digital Twin 3D
        </h2>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-500">{rpm.toFixed(1)} rpm</span>
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${theme.badge}`}>
            {theme.label}
          </span>
        </div>
      </div>
      <div className="h-[360px] w-full">
        <Canvas
          shadows
          camera={{ position: [2.35, 1.55, 2.55], fov: 42 }}
          dpr={[1, 2]}
          gl={{ toneMappingExposure: 1.35 }}
        >
          <MotorScene rpm={rpm} statusColor={theme.hex} />
        </Canvas>
      </div>
    </section>
  )
}
