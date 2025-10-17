"""Styling and UI helper functions."""
import plotly.graph_objects as go


def apply_fig_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    """Apply dark theme to plotly figures"""
    fig.update_layout(
        height=height,
        paper_bgcolor="#1e293b",
        plot_bgcolor="#0f172a",
        font=dict(family="Inter, sans-serif", color="#f1f5f9", size=12),
        margin=dict(l=60, r=40, t=60, b=50),
        title_font=dict(size=18, color="#f1f5f9"),
        legend=dict(
            bgcolor="rgba(30,41,59,0.9)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=11, color="#cbd5e1")
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#f1f5f9",
            bordercolor="#334155"
        )
    )
    
    # Update axes for dark theme
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#334155',
        showline=True,
        linewidth=1,
        linecolor='#475569',
        color='#cbd5e1'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#334155',
        showline=True,
        linewidth=1,
        linecolor='#475569',
        color='#cbd5e1'
    )
    
    return fig


def create_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Create a modern metric card with gradient background"""
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_color == "normal" or "+" in delta else "negative"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'
    
    return f"""
    <div class="card card-gradient" style="text-align: center;">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """


def create_section_header(icon: str, title: str, subtitle: str = None):
    """Create a modern section header with icon"""
    subtitle_html = f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ""
    return f"""
    <h2 class="section-title">
        <span style="font-size: 1.5rem;">{icon}</span>
        {title}
    </h2>
    {subtitle_html}
    """


def create_insight_card(title: str, message: str, icon: str = ""):
    """Create an insight card with modern styling"""
    icon_display = f"{icon} " if icon else ""
    return f"""
    <div class="card" style="border-left: 4px solid #3b82f6; background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);">
        <h4 style="color: #f1f5f9; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
            {icon_display}{title}
        </h4>
        <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0;">
            {message}
        </p>
    </div>
    """


def get_growth_color_style(growth_rate):
    """Generate darker, solid color gradients based on growth rate for dark theme"""
    growth_pct = growth_rate * 100
    
    if growth_pct >= 50:
        return {
            "bg": "linear-gradient(135deg, #065f46 0%, #047857 100%)",
            "border": "#10b981",
            "icon": "▲▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#6ee7b7"
        }
    elif growth_pct >= 20:
        return {
            "bg": "linear-gradient(135deg, #047857 0%, #059669 100%)",
            "border": "#34d399",
            "icon": "▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#a7f3d0"
        }
    elif growth_pct >= 5:
        return {
            "bg": "linear-gradient(135deg, #059669 0%, #10b981 100%)",
            "border": "#6ee7b7",
            "icon": "▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#d1fae5"
        }
    elif growth_pct >= 0:
        return {
            "bg": "linear-gradient(135deg, #10b981 0%, #34d399 100%)",
            "border": "#a7f3d0",
            "icon": "→",
            "label": f"+{growth_pct:.1f}%",
            "color": "#ffffff",
            "icon_color": "#d1fae5"
        }
    elif growth_pct >= -5:
        return {
            "bg": "linear-gradient(135deg, #dc2626 0%, #ef4444 100%)",
            "border": "#fca5a5",
            "icon": "→",
            "label": f"{growth_pct:.1f}%",
            "color": "#ffffff",
            "icon_color": "#fecaca"
        }
    elif growth_pct >= -20:
        return {
            "bg": "linear-gradient(135deg, #b91c1c 0%, #dc2626 100%)",
            "border": "#f87171",
            "icon": "▼",
            "label": f"{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#fca5a5"
        }
    else:
        return {
            "bg": "linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)",
            "border": "#ef4444",
            "icon": "▼▼",
            "label": f"{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#f87171"
        }
