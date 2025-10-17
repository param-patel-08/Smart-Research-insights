"""Visualization functions for creating charts and graphs."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def create_sunburst_chart(df, mapping):
    """Create hierarchical sunburst: Theme > Sub-theme > Topic"""
    # Build hierarchy data - ensure we capture ALL themes and sub-themes
    hierarchy_data = []
    
    for _, row in df.iterrows():
        topic_id = str(row['topic_id'])
        parent_theme = row['theme']
        sub_theme = row.get('sub_theme')
        
        # Use 'Other' only if sub_theme is truly missing
        if pd.isna(sub_theme) or sub_theme == '' or sub_theme is None:
            sub_theme = 'Other'
        
        hierarchy_data.append({
            'parent_theme': parent_theme,
            'sub_theme': sub_theme,
            'topic_id': topic_id,
            'count': 1
        })
    
    hierarchy_df = pd.DataFrame(hierarchy_data)
    
    # Aggregate counts at each level
    theme_counts = hierarchy_df.groupby(['parent_theme']).size().reset_index(name='count')
    subtheme_counts = hierarchy_df.groupby(['parent_theme', 'sub_theme']).size().reset_index(name='count')
    
    # Build sunburst data structure
    labels = []
    parents = []
    values = []
    colors = []
    
    # Blue shades palette for themes (1st outer ring) - all blue shades matching theme
    blue_shades = [
        '#1e40af', '#2563eb', '#3b82f6', '#60a5fa',
        '#0ea5e9', '#06b6d4', '#0891b2', '#0284c7',
        '#1d4ed8', '#1e3a8a', '#2dd4bf', '#0e7490',
    ]
    
    theme_colors = {}
    
    # Add root
    labels.append('All Research')
    parents.append('')
    values.append(len(df))
    colors.append('#1e293b')  # Dark background for root
    
    # Add ALL themes (parent level) - 1st outer ring with blue shades
    for i, (_, row) in enumerate(theme_counts.iterrows()):
        theme_name = row['parent_theme'].replace('_', ' ').title()
        labels.append(theme_name)
        parents.append('All Research')
        values.append(row['count'])
        theme_color = blue_shades[i % len(blue_shades)]
        colors.append(theme_color)
        theme_colors[row['parent_theme']] = theme_color
    
    # Add ALL sub-themes (middle level) - 2nd outer ring with gradients from dark to light
    for parent_theme in subtheme_counts['parent_theme'].unique():
        theme_subthemes = subtheme_counts[subtheme_counts['parent_theme'] == parent_theme].copy()
        theme_subthemes = theme_subthemes.sort_values('count', ascending=False)
        
        base_color = theme_colors.get(parent_theme, blue_shades[0])
        num_subthemes = len(theme_subthemes)
        
        for idx, (_, row) in enumerate(theme_subthemes.iterrows()):
            sub_name = row['sub_theme'].replace('_', ' ').title()
            parent_name = row['parent_theme'].replace('_', ' ').title()
            labels.append(sub_name)
            parents.append(parent_name)
            values.append(row['count'])
            
            # Create gradient: darkest for most papers, lightest for least papers
            if num_subthemes > 1:
                brightness_factor = 1.0 - (idx / (num_subthemes - 1)) * 0.6
            else:
                brightness_factor = 1.0
            
            # Convert hex to RGB, adjust brightness, convert back
            hex_color = base_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = int(r * brightness_factor + 255 * (1 - brightness_factor))
            g = int(g * brightness_factor + 255 * (1 - brightness_factor))
            b = int(b * brightness_factor + 255 * (1 - brightness_factor))
            
            gradient_color = f'#{r:02x}{g:02x}{b:02x}'
            colors.append(gradient_color)
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(color='#0f172a', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>Papers: %{value}<br>%{percentParent} of parent<extra></extra>',
        maxdepth=2,
        textfont=dict(color='#ffffff', size=11)
    ))
    
    fig.update_layout(
        title=" ",
        height=650,
        font=dict(size=11, color='#f1f5f9'),
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        title_font=dict(size=18, color='#f1f5f9')
    )
    
    return fig


def create_sankey_flow(df):
    """Sankey diagram: Theme → Sub-Theme → University"""
    top_unis = df['university'].value_counts().head(10).index
    top_subthemes = df['sub_theme'].value_counts().head(15).index
    
    df_filtered = df[df['university'].isin(top_unis) & df['sub_theme'].isin(top_subthemes)]
    
    themes = df_filtered['theme'].unique()
    subthemes = df_filtered['sub_theme'].unique()
    unis = top_unis
    
    all_labels = (
        [t.replace('_', ' ') for t in themes] + 
        [s.replace('_', ' ') for s in subthemes] + 
        list(unis)
    )
    
    label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
    
    sources = []
    targets = []
    values = []
    
    # Theme → Sub-theme flows
    for theme in themes:
        theme_label = theme.replace('_', ' ')
        for subtheme in subthemes:
            subtheme_label = subtheme.replace('_', ' ')
            count = len(df_filtered[(df_filtered['theme'] == theme) & (df_filtered['sub_theme'] == subtheme)])
            if count > 0:
                sources.append(label_to_idx[theme_label])
                targets.append(label_to_idx[subtheme_label])
                values.append(count)
    
    # Sub-theme → University flows
    for subtheme in subthemes:
        subtheme_label = subtheme.replace('_', ' ')
        for uni in unis:
            count = len(df_filtered[(df_filtered['sub_theme'] == subtheme) & (df_filtered['university'] == uni)])
            if count > 0:
                sources.append(label_to_idx[subtheme_label])
                targets.append(label_to_idx[uni])
                values.append(count)
    
    # Create color palette for nodes
    num_themes = len(themes)
    num_subthemes = len(subthemes)
    num_unis = len(unis)
    
    theme_colors = ['#3b82f6', '#2563eb', '#06b6d4', '#8b5cf6', '#60a5fa', 
                    '#0ea5e9', '#a78bfa', '#0284c7', '#7c3aed', '#6366f1'] * 10
    subtheme_colors = ['#60a5fa', '#93c5fd', '#7dd3fc', '#c4b5fd'] * 20
    uni_colors = ['#22d3ee', '#06b6d4', '#0891b2'] * 20
    
    node_colors = (theme_colors[:num_themes] + 
                   subtheme_colors[:num_subthemes] + 
                   uni_colors[:num_unis])
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#0f172a", width=1),
            label=all_labels,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(59, 130, 246, 0.3)'
        )
    )])
    
    fig.update_layout(
        title="Research Flow: Themes → Sub-Themes → Top Universities",
        height=700,
        font=dict(size=10, color='#f1f5f9'),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        title_font=dict(size=18, color='#f1f5f9')
    )
    
    return fig


def create_trend_timeline(df):
    """Advanced timeline with trend analysis"""
    df_copy = df.copy()
    df_copy['year_month'] = df_copy['date'].dt.to_period('M')
    
    monthly_counts = df_copy.groupby(['year_month', 'theme']).size().reset_index(name='count')
    monthly_counts['year_month'] = monthly_counts['year_month'].dt.to_timestamp()
    
    blue_palette = [
        '#3b82f6', '#2563eb', '#06b6d4', '#8b5cf6', '#60a5fa',
        '#0ea5e9', '#a78bfa', '#0284c7', '#7c3aed', '#6366f1'
    ]
    
    fig = px.area(
        monthly_counts,
        x='year_month',
        y='count',
        color='theme',
        title="Research Publication Trends Over Time",
        labels={'year_month': 'Date', 'count': 'Papers Published', 'theme': 'Theme'},
        color_discrete_sequence=blue_palette
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
            bgcolor='rgba(30,41,59,0.9)', bordercolor='#334155', borderwidth=1,
            font=dict(size=11, color='#cbd5e1')
        ),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        font=dict(family='Inter, sans-serif', color='#f1f5f9', size=12),
        title_font=dict(size=18, color='#f1f5f9'),
        xaxis=dict(
            showgrid=True, gridwidth=1, gridcolor='#334155',
            showline=True, linewidth=1, linecolor='#475569', color='#cbd5e1'
        ),
        yaxis=dict(
            showgrid=True, gridwidth=1, gridcolor='#334155',
            showline=True, linewidth=1, linecolor='#475569', color='#cbd5e1'
        )
    )
    
    return fig


def create_growth_heatmap(df):
    """Create time-series heatmap showing sub-theme growth"""
    df_copy = df.copy()
    df_copy['year_quarter'] = df_copy['date'].dt.to_period('Q').astype(str)
    
    heatmap_data = df_copy.groupby(['sub_theme', 'year_quarter']).size().unstack(fill_value=0)
    active_subthemes = heatmap_data.sum(axis=1).nlargest(15).index
    heatmap_data = heatmap_data.loc[active_subthemes]
    heatmap_data.index = [idx.replace('_', ' ') for idx in heatmap_data.index]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        text=heatmap_data.values,
        texttemplate='%{text}',
        textfont={"size": 8},
        hovertemplate='<b>%{y}</b><br>%{x}<br>Papers: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Sub-Theme Activity Over Time (Quarterly)",
        xaxis_title="Quarter",
        yaxis_title="Sub-Theme",
        height=500,
        font=dict(size=10)
    )
    
    return fig


def create_impact_bubble_chart(df, mapping):
    """Bubble chart: Growth vs Citations vs Volume"""
    df_copy = df.copy()
    df_copy['year'] = df_copy['date'].dt.year
    
    metrics = []
    for sub_theme in df_copy['sub_theme'].dropna().unique():
        sub_df = df_copy[df_copy['sub_theme'] == sub_theme]
        
        if len(sub_df) < 5:
            continue
        
        growth_2023 = len(sub_df[sub_df['year'] == 2023])
        growth_2024 = len(sub_df[sub_df['year'] == 2024])
        growth_rate = ((growth_2024 - growth_2023) / (growth_2023 + 1)) * 100 if growth_2023 > 0 else 0
        avg_citations = sub_df['citations'].mean()
        parent_theme = sub_df['theme'].mode()[0] if len(sub_df) > 0 else 'Other'
        
        metrics.append({
            'sub_theme': sub_theme.replace('_', ' '),
            'growth_rate': growth_rate,
            'avg_citations': avg_citations,
            'paper_count': len(sub_df),
            'parent_theme': parent_theme.replace('_', ' ')
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    fig = px.scatter(
        metrics_df,
        x='growth_rate',
        y='avg_citations',
        size='paper_count',
        color='parent_theme',
        hover_name='sub_theme',
        hover_data={'growth_rate': ':.1f%', 'avg_citations': ':.0f', 'paper_count': True},
        labels={
            'growth_rate': 'Growth Rate 2023→2024 (%)',
            'avg_citations': 'Average Citations',
            'paper_count': 'Papers',
            'parent_theme': 'Theme'
        },
        title="Sub-Theme Impact Analysis: Growth vs Citations",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(height=550, showlegend=True)
    
    median_growth = metrics_df['growth_rate'].median()
    median_citations = metrics_df['avg_citations'].median()
    fig.add_hline(y=median_citations, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=median_growth, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_university_radar(df, selected_unis):
    """Radar chart comparing universities across sub-themes"""
    if not selected_unis or len(selected_unis) < 2:
        return None
    
    top_subthemes = df['sub_theme'].value_counts().head(10).index
    fig = go.Figure()
    
    for uni in selected_unis[:5]:
        uni_data = df[df['university'] == uni]
        counts = []
        for subtheme in top_subthemes:
            count = len(uni_data[uni_data['sub_theme'] == subtheme])
            counts.append(count)
        
        fig.add_trace(go.Scatterpolar(
            r=counts,
            theta=[s.replace('_', ' ')[:20] for s in top_subthemes],
            fill='toself',
            name=uni
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        title="University Research Profile Comparison",
        height=500
    )
    
    return fig
