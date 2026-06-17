import { AlertTriangle, X, Check } from 'lucide-react';

interface Props {
    title: string;
    message: string;
    danger?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({ title, message, danger = false, onConfirm, onCancel }: Props) {
    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-3 mb-4">
                    <div style={{
                        width: 36, height: 36, borderRadius: '50%',
                        background: danger ? 'var(--red-dim)' : 'var(--amber-dim)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: `1px solid ${danger ? 'rgba(239,68,68,0.3)' : 'rgba(245,158,11,0.3)'}`,
                        flexShrink: 0,
                    }}>
                        <AlertTriangle size={18} color={danger ? 'var(--red)' : 'var(--amber)'} />
                    </div>
                    <h3 style={{ color: danger ? 'var(--red)' : 'var(--amber)' }}>{title}</h3>
                </div>
                <p>{message}</p>
                <div className="modal-actions">
                    <button className="btn btn-ghost" onClick={onCancel}>
                        <X size={14} /> Cancel
                    </button>
                    <button className={`btn ${danger ? 'btn-danger' : 'btn-warning'}`} onClick={onConfirm}>
                        <Check size={14} /> Confirm
                    </button>
                </div>
            </div>
        </div>
    );
}
