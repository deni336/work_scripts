document.addEventListener("DOMContentLoaded", function() {
  let i = 0,
      duration = 750;

  // DOM references
  const ctx          = document.getElementById('fmcChart').getContext('2d');
  const ctxNMC       = document.getElementById('nmcChart').getContext('2d');
  let statusChart    = null;
  let nmcChart       = null;
  const mcRateDiv    = d3.select("#mcRate");
  const mcTitle      = d3.select("#mcTitle");
  const mdsSelect    = d3.select("#mdsFilter");
  const baseSelect   = d3.select("#baseFilter");
  const statusSelect = d3.select("#statusFilter");
  const dfContainer  = d3.select("#aircraft-table");

  // Status prefixes & colors for the pie chart
  const ALLOWED_PREFIXES = ["FMC", "PMC", "NMC"];
  const STATUS_COLORS = {
    FMC: "#00308F",  // Air Force Blue
    PMC: "#fffb00",  // Cloud Gray
    NMC: "#a00000"   // Muted Dark Red
  };
  const NMC_COLORS = {
    NMCM: "#e74c3c",
    NMCS: "#f39c12",
    NMCB: "#8e44ad"
  };

  // Current data & entity
  let currentData   = [];
  let currentEntity = "";

  // Columns for the aircraft table
  const columns = [
    { key: "aircraft_serial_number",   label: "Ser No"    },
    { key: "mission_design_series",    label: "MDS"       },
    { key: "current_assigned_base",    label: "Base"      },
    { key: "current_condition_detail", label: "Status"    },
    { key: "assigned_unit_pas",        label: "Pas"       }
  ];

  function updateStatusChart(counts) {
    const labels = [], data = [], backgroundColor = [];
    const keys = ["FMC", "PMC", "NMC"];
    const total = keys.reduce((sum, k) => sum + (counts[k] || 0), 0) || 1;
  
    keys.forEach(k => {
      const count = counts[k] || 0;
      const pct = ((count / total) * 100).toFixed(1);
      labels.push(`${k} (${pct}% - ${count})`);
      data.push(count);
      backgroundColor.push(STATUS_COLORS[k]);
    });
  
    if (statusChart) statusChart.destroy();
    statusChart = new Chart(ctx, {
      type: 'pie',
      data: { labels, datasets: [{ data, backgroundColor }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              generateLabels: chart => chart.data.labels.map((label, i) => ({
                text: label,
                fillStyle: chart.data.datasets[0].backgroundColor[i],
                strokeStyle: chart.data.datasets[0].backgroundColor[i],
                index: i
              }))
            }
          }
        }
      }
    });
  }

  function updateNMCChart(counts) {
    const labels = [], data = [], backgroundColor = [];
    const keys = ["NMCM", "NMCS", "NMCB"];
    const total = keys.reduce((sum, k) => sum + (counts[k] || 0), 0) || 1;
  
    keys.forEach(k => {
      const count = counts[k] || 0;
      const pct = ((count / total) * 100).toFixed(1);
      labels.push(`${k} (${pct}% - ${count})`);
      data.push(count);
      backgroundColor.push(NMC_COLORS[k]);
    });
  
    if (nmcChart) nmcChart.destroy();
    nmcChart = new Chart(ctxNMC, {
      type: 'pie',
      data: { labels, datasets: [{ data, backgroundColor }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              generateLabels: chart => chart.data.labels.map((label, i) => ({
                text: label,
                fillStyle: chart.data.datasets[0].backgroundColor[i],
                strokeStyle: chart.data.datasets[0].backgroundColor[i],
                index: i
              }))
            }
          }
        }
      }
    });
  }

  function populateFilters(data) {
    const mdsSet = Array.from(new Set(data.map(r => r.mission_design_series).filter(v => v))).sort();
    mdsSelect.html('<option value="">All</option>');
    mdsSet.forEach(mds => mdsSelect.append("option").attr("value", mds).text(mds));

    const baseSet = Array.from(new Set(data.map(r => r.current_assigned_base).filter(v => v))).sort();
    baseSelect.html('<option value="">All</option>');
    baseSet.forEach(b => baseSelect.append("option").attr("value", b).text(b));

    const statusSet = Array.from(new Set(data.map(r => r.current_condition_detail).filter(v => v))).sort();
    statusSelect.html('<option value="">All</option>');
    statusSet.forEach(s => statusSelect.append("option").attr("value", s).text(s));
  }

    // Render the table, pie chart, and mission capable rate based on filters
    function renderDetails() {
      const selMds    = mdsSelect.property("value");
      const selBase   = baseSelect.property("value");
      const selStatus = statusSelect.property("value");
  
      const filtered = currentData.filter(r => {
        const status = (r.current_condition_detail || "").toLowerCase();
        const location = (r.location || "").toLowerCase();
      
        // Exclude any rows with 'tran' in status or 'in storage' in location
        if (status.includes("tran") || location.includes("in storage")) return false;
      
        return (!selMds    || r.mission_design_series    === selMds) &&
               (!selBase   || r.current_assigned_base    === selBase) &&
               (!selStatus || r.current_condition_detail === selStatus);
      });
      
  
      // Show total count above the table
      const total = filtered.length;
      dfContainer.html(`<div id="totalCount"><strong>Total Aircraft Assigned: ${total}</strong></div>`);
  
      if (!total) {
        dfContainer.append("p").text("No aircraft match these filters.");
        updateStatusChart({});
        updateNMCChart({});
        mcRateDiv.text("0.0%");
        return;
      }
  
      // Build the table
      const table = dfContainer.append("table");
      const thead = table.append("thead").append("tr");
      columns.forEach(c => thead.append("th").text(c.label));
      const tbody = table.append("tbody");
  
      // Count statuses for pie chart
      const counts = { FMC: 0, PMC: 0, NMC: 0 };
      const nmcTypes = { NMCM: 0, NMCS: 0, NMCB: 0 };
  
      filtered.forEach(r => {
        const st = (r.current_condition_detail || "").toUpperCase();
        const p = ALLOWED_PREFIXES.find(pref => st.startsWith(pref));
        if (p) counts[p]++;
  
        if (st.startsWith("NMCM")) nmcTypes.NMCM++;
        if (st.startsWith("NMCS")) nmcTypes.NMCS++;
        if (st.startsWith("NMCB")) nmcTypes.NMCB++;
  
        // Append row
        const tr = tbody.append("tr");
        columns.forEach(c => {
          tr.append("td").text(r[c.key] != null ? r[c.key] : "");
        });
      });
  
      // Update pie charts
      updateStatusChart(counts);
      updateNMCChart(nmcTypes);
  
      // Compute and display mission capable rate
      const mc = counts.FMC + counts.PMC;
      mcRateDiv.text(((mc / total) * 100).toFixed(1) + "%");
    }
  
    // Load aircraft data for a given list of PAS codes and entity name
    function loadAircraft(pasList, entityName) {
      currentEntity = entityName;
      mcTitle.text(`Mission Capable Rate - ${entityName}`);
      dfContainer.html("Loading…");
      mcRateDiv.text("--%");
  
      fetch("/api/aircraft?pas_list=" + encodeURIComponent(JSON.stringify(pasList)))
        .then(r => r.json())
        .then(data => {
          currentData = data;
          populateFilters(data);
          // Reset filters
          mdsSelect.property("value", "");
          baseSelect.property("value", "");
          statusSelect.property("value", "");
          renderDetails();
        })
        .catch(err => {
          dfContainer.html("<p class='error'>Fetch error</p>");
          console.error(err);
        });
    }
  
    // Wire up filter change events
    mdsSelect.on("change", renderDetails);
    baseSelect.on("change", renderDetails);
    statusSelect.on("change", renderDetails);
    // Collect PAS codes recursively from a tree node
    function collectPas(node, arr) {
      arr.push(node.data.PAS);
      const kids = node.children || node._children;
      if (kids) kids.forEach(c => collectPas(c, arr));
    }
  
    // Render the D3 tree and auto‐load the root node
    fetch("/data/tree.json?nocache=" + Date.now())
      .then(r => r.json())
      .then(treeData => {
        const margin = { top: 20, right: 120, bottom: 20, left: 120 },
              width  = window.innerWidth * 0.5 - margin.left - margin.right,
              height = window.innerHeight    - margin.top  - margin.bottom;
  
        const svg = d3.select("#tree-container").append("svg")
            .attr("width",  width  + margin.left + margin.right)
            .attr("height", height + margin.top  + margin.bottom)
            .call(d3.zoom().scaleExtent([0.1, 3]).on("zoom", zoomed));
  
        const g = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
  
        function zoomed() {
          const t = d3.event.transform;
          g.attr("transform", t);
          g.selectAll("text").attr("transform", `scale(${1 / t.k})`);
        }
  
        const treemap = d3.tree().size([height, width]);
        const root = d3.hierarchy(treeData, d => d.Children);
        root.x0 = height / 2;
        root.y0 = 0;
  
        if (root.children) root.children.forEach(collapse);
        update(root);
  
        // Auto‐load root node on page load
        const rootLabel = root.data.label || "";
        const parts = rootLabel.split(" - ");
        const entityName = parts.length > 1 ? parts.slice(1).join(" - ") : rootLabel;
        const pasList = [];
        collectPas(root, pasList);
        loadAircraft(pasList, entityName);
  
        function collapse(d) {
          if (d.children) {
            d._children = d.children;
            d._children.forEach(collapse);
            d.children = null;
          }
        }
  
        function update(source) {
          const treeDataLayout = treemap(root);
          const nodes = treeDataLayout.descendants(),
                links = nodes.slice(1);
  
          nodes.forEach(d => d.y = d.depth * 180);
  
          // NODES
          const node = g.selectAll("g.node")
              .data(nodes, d => d.id || (d.id = ++i));
  
          const nodeEnter = node.enter().append("g")
              .attr("class", "node")
              .attr("transform", d => `translate(${source.y0},${source.x0})`)
              .on("click", d => {
                click(d);
                const lbl = d.data.label || "";
                const parts = lbl.split(" - ");
                const name = parts.length > 1 ? parts.slice(1).join(" - ") : lbl;
                const pasList = [];
                collectPas(d, pasList);
                loadAircraft(pasList, name);
              });
  
          nodeEnter.append("circle")
              .attr("r", 1e-6)
              .style("fill", d => d._children ? "lightsteelblue" : "#fff");
  
          nodeEnter.append("text")
              .attr("dy", ".35em")
              .attr("x", d => d.children || d._children ? -13 : 13)
              .attr("text-anchor", d => d.children || d._children ? "end" : "start")
              .text(d => {
                const lbl = d.data.label || "";
                const parts = lbl.split(" - ");
                return parts.length > 1 ? parts.slice(1).join(" - ") : lbl;
              })
              .style("cursor", "pointer");
  
          const nodeUpdate = nodeEnter.merge(node);
          nodeUpdate.transition().duration(duration)
              .attr("transform", d => `translate(${d.y},${d.x})`);
          nodeUpdate.select("circle")
              .attr("r", 10)
              .style("fill", d => d._children ? "lightsteelblue" : "#fff");
  
          const nodeExit = node.exit().transition().duration(duration)
              .attr("transform", d => `translate(${source.y},${source.x})`)
              .remove();
          nodeExit.select("circle").attr("r", 1e-6);
          nodeExit.select("text").style("fill-opacity", 1e-6);
  
          // LINKS
          const link = g.selectAll("path.link")
              .data(links, d => d.id);
          const linkEnter = link.enter().insert("path", "g")
              .attr("class", "link")
              .attr("d", d => {
                const o = { x: source.x0, y: source.y0 };
                return diagonal(o, o);
              });
          linkEnter.merge(link).transition().duration(duration)
              .attr("d", d => diagonal(d.parent, d));
          link.exit().transition().duration(duration)
              .attr("d", d => {
                const o = { x: source.x, y: source.y };
                return diagonal(o, o);
              })
              .remove();
  
          nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
        }
  
        function diagonal(s, d) {
          return `M ${s.y} ${s.x}
                  C ${(s.y + d.y)/2} ${s.x},
                    ${(s.y + d.y)/2} ${d.x},
                    ${d.y} ${d.x}`;
        }
  
        function click(d) {
          if (d.children) {
            d._children = d.children;
            d.children = null;
          } else {
            d.children = d._children;
            d._children = null;
          }
          update(d);
        }
      })
      .catch(err => console.error("Failed to load tree data:", err));
  });
  