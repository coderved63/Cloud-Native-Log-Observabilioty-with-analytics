import numpy as np


class VMPlacementOptimizer:
    """Optimizes VM-to-host placement using First Fit Decreasing bin packing."""

    def __init__(self, host_cpu_capacity=10000, host_memory_capacity_mb=65536, cpu_threshold=0.8, memory_threshold=0.8):
        self.host_cpu_capacity = host_cpu_capacity       # MHz per host
        self.host_memory_capacity = host_memory_capacity_mb  # MB per host
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def optimize(self, vm_summaries):
        """Run First Fit Decreasing bin packing to find optimal VM placement."""
        if not vm_summaries:
            return {'hosts': [], 'total_hosts': 0, 'efficiency': {}}

        # Sort VMs by CPU usage descending (FFD)
        sorted_vms = sorted(vm_summaries, key=lambda v: v['avg_cpu_usage_mhz'], reverse=True)

        hosts = []

        for vm in sorted_vms:
            cpu_need = vm['avg_cpu_usage_mhz']
            mem_need = vm.get('avg_memory_usage_mb', vm.get('avg_memory_provisioned_mb', 0))

            placed = False
            for host in hosts:
                remaining_cpu = self.host_cpu_capacity * self.cpu_threshold - host['cpu_used']
                remaining_mem = self.host_memory_capacity * self.memory_threshold - host['memory_used']

                if cpu_need <= remaining_cpu and mem_need <= remaining_mem:
                    host['vms'].append(vm['vm_name'])
                    host['cpu_used'] += cpu_need
                    host['memory_used'] += mem_need
                    placed = True
                    break

            if not placed:
                hosts.append({
                    'host_id': f"host-{len(hosts) + 1}",
                    'vms': [vm['vm_name']],
                    'cpu_used': cpu_need,
                    'memory_used': mem_need,
                    'cpu_capacity': self.host_cpu_capacity,
                    'memory_capacity': self.host_memory_capacity,
                })

        # Calculate efficiency metrics
        total_cpu_used = sum(h['cpu_used'] for h in hosts)
        total_cpu_available = len(hosts) * self.host_cpu_capacity
        total_mem_used = sum(h['memory_used'] for h in hosts)
        total_mem_available = len(hosts) * self.host_memory_capacity

        # Format host results
        host_results = []
        for h in hosts:
            host_results.append({
                'host_id': h['host_id'],
                'vm_count': len(h['vms']),
                'vms': h['vms'],
                'cpu_used_mhz': round(h['cpu_used'], 1),
                'cpu_capacity_mhz': h['cpu_capacity'],
                'cpu_utilization_pct': round(h['cpu_used'] / h['cpu_capacity'] * 100, 1),
                'memory_used_mb': round(h['memory_used'], 1),
                'memory_capacity_mb': h['memory_capacity'],
                'memory_utilization_pct': round(h['memory_used'] / h['memory_capacity'] * 100, 1),
            })

        # Naive placement comparison (1 VM per host)
        naive_hosts = len(sorted_vms)

        return {
            'hosts': host_results,
            'total_hosts_needed': len(hosts),
            'total_vms_placed': len(sorted_vms),
            'naive_hosts_needed': naive_hosts,
            'hosts_saved': naive_hosts - len(hosts),
            'consolidation_ratio': round(len(sorted_vms) / len(hosts), 2) if hosts else 0,
            'efficiency': {
                'overall_cpu_utilization': round(total_cpu_used / total_cpu_available * 100, 1) if total_cpu_available > 0 else 0,
                'overall_memory_utilization': round(total_mem_used / total_mem_available * 100, 1) if total_mem_available > 0 else 0,
                'cpu_waste_pct': round((1 - total_cpu_used / total_cpu_available) * 100, 1) if total_cpu_available > 0 else 0,
                'memory_waste_pct': round((1 - total_mem_used / total_mem_available) * 100, 1) if total_mem_available > 0 else 0,
            }
        }

    def get_efficiency_analysis(self, vm_summaries):
        """Analyze resource waste — provisioned vs actually used."""
        if not vm_summaries:
            return {}

        total_cpu_provisioned = sum(v['cpu_capacity_mhz'] for v in vm_summaries)
        total_cpu_used = sum(v['avg_cpu_usage_mhz'] for v in vm_summaries)
        total_mem_provisioned = sum(v['avg_memory_provisioned_mb'] for v in vm_summaries)
        total_mem_used = sum(v['avg_memory_usage_mb'] for v in vm_summaries)

        # Per-VM efficiency
        overprovisioned = []
        underprovisioned = []
        for v in vm_summaries:
            if v['avg_cpu_utilization'] < 10 and v['avg_memory_utilization'] < 10:
                overprovisioned.append({
                    'vm_name': v['vm_name'],
                    'cpu_utilization': round(v['avg_cpu_utilization'], 1),
                    'memory_utilization': round(v['avg_memory_utilization'], 1),
                    'recommendation': 'downsize or decommission',
                })
            elif v['avg_cpu_utilization'] > 85 or v['avg_memory_utilization'] > 85:
                underprovisioned.append({
                    'vm_name': v['vm_name'],
                    'cpu_utilization': round(v['avg_cpu_utilization'], 1),
                    'memory_utilization': round(v['avg_memory_utilization'], 1),
                    'recommendation': 'scale up resources',
                })

        return {
            'total_vms': len(vm_summaries),
            'cpu_provisioned_mhz': round(total_cpu_provisioned, 1),
            'cpu_used_mhz': round(total_cpu_used, 1),
            'cpu_waste_pct': round((1 - total_cpu_used / total_cpu_provisioned) * 100, 1) if total_cpu_provisioned > 0 else 0,
            'memory_provisioned_mb': round(total_mem_provisioned, 1),
            'memory_used_mb': round(total_mem_used, 1),
            'memory_waste_pct': round((1 - total_mem_used / total_mem_provisioned) * 100, 1) if total_mem_provisioned > 0 else 0,
            'overprovisioned_vms': overprovisioned[:10],
            'underprovisioned_vms': underprovisioned[:10],
            'overprovisioned_count': len(overprovisioned),
            'underprovisioned_count': len(underprovisioned),
            'right_sized_count': len(vm_summaries) - len(overprovisioned) - len(underprovisioned),
        }
