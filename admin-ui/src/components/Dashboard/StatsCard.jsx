export default function StatsCard({ icon, label, value, color = "", onClick }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 flex items-center gap-4" onClick={onClick}>
      <div className={`p-3 rounded-full ${color}`}>{icon}</div>
      <div>
        <h3 className="text-2xl font-bold leading-none">{value}</h3>
        <p className="text-sm text-gray-600 mt-1">{label}</p>
      </div>
    </div>
  );
}
