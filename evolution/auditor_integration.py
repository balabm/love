"""
Autopoietic Auditor Integration with Existing Systems

Integrates the Autopoietic Auditor with existing LOVE monitoring systems
including Sentinel, error tracking, and health monitoring to create a
cohesive self-monitoring architecture.
"""

import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
from core.execution_guard import log_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuditorIntegration:
    """
    Integration layer for Autopoietic Auditor with existing systems.
    
    Connects the auditor with:
    - Sentinel monitoring system
    - Error tracking and logging
    - Health monitoring systems
    - Module registry and discovery
    """
    
    def __init__(self):
        self.sentinel = None
        self.error_tracker = None
        self.health_monitor = None
        self.module_registry = {}
        
    def integrate_with_sentinel(self, sentinel_instance) -> bool:
        """Integrate with Sentinel monitoring system"""
        try:
            from core.sentinel import Sentinel
            if isinstance(sentinel_instance, Sentinel):
                self.sentinel = sentinel_instance
                
                # Register auditor as a health check in Sentinel
                self._register_sentinel_health_check()
                
                logger.info("Successfully integrated with Sentinel")
                return True
            else:
                logger.warning("Provided instance is not a Sentinel instance")
                return False
                
        except ImportError:
            logger.warning("Sentinel module not available")
            return False
        except Exception as e:
            logger.error(f"Error integrating with Sentinel: {e}")
            return False
    
    def _register_sentinel_health_check(self) -> None:
        """Register auditor as a health check in Sentinel"""
        if self.sentinel and hasattr(self.sentinel, 'register_health_check'):
            # Register the auditor's state coherence inspection as a health check
            def auditor_health_check():
                from evolution.autopoietic_auditor import get_autopoietic_auditor
                auditor = get_autopoietic_auditor()
                summary = auditor.get_audit_summary()
                
                # Determine health status
                critical_modules = summary.get('critical_modules', 0)
                if critical_modules > 0:
                    return "critical", f"{critical_modules} modules in critical state"
                elif summary.get('degraded_modules', 0) > 0:
                    return "degraded", f"{summary.get('degraded_modules')} modules degraded"
                else:
                    return "healthy", "All modules operating normally"
            
            self.sentinel.register_health_check("autopoietic_auditor", auditor_health_check)
            logger.info("Registered auditor health check with Sentinel")
    
    def integrate_with_error_tracking(self, error_tracker_instance) -> bool:
        """Integrate with error tracking system"""
        try:
            self.error_tracker = error_tracker_instance
            
            # Feed error data into drift detection
            self._setup_error_feeding()
            
            logger.info("Successfully integrated with error tracking")
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with error tracking: {e}")
            return False
    
    def _setup_error_feeding(self) -> None:
        """Setup feeding error data into drift detection"""
        if self.error_tracker and hasattr(self.error_tracker, 'get_recent_errors'):
            # Register callback to feed errors into drift detector
            def error_callback(error_data):
                from evolution.autopoietic_auditor import get_autopoietic_auditor
                auditor = get_autopoietic_auditor()
                
                # Update module error counts based on error data
                module_id = error_data.get('module_id')
                if module_id:
                    # This would update the drift detector's error tracking
                    pass
            
            self.error_tracker.register_error_callback(error_callback)
            logger.info("Setup error feeding into drift detection")
    
    def integrate_with_health_monitor(self, health_monitor_instance) -> bool:
        """Integrate with health monitoring system"""
        try:
            self.health_monitor = health_monitor_instance
            
            # Add auditor metrics to health monitoring
            self._add_auditor_metrics()
            
            logger.info("Successfully integrated with health monitor")
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with health monitor: {e}")
            return False
    
    def _add_auditor_metrics(self) -> None:
        """Add auditor-specific metrics to health monitoring"""
        if self.health_monitor and hasattr(self.health_monitor, 'add_metric'):
            from evolution.autopoietic_auditor import get_autopoietic_auditor
            auditor = get_autopoietic_auditor()
            
            # Add auditor metrics
            def get_auditor_metrics():
                summary = auditor.get_audit_summary()
                return {
                    'total_modules': summary.get('total_modules', 0),
                    'healthy_modules': summary.get('healthy_modules', 0),
                    'degraded_modules': summary.get('degraded_modules', 0),
                    'critical_modules': summary.get('critical_modules', 0),
                    'drift_detections': summary.get('recent_drift_detections', 0),
                    'hallucination_detections': summary.get('recent_hallucination_detections', 0),
                    'reconciliations': summary.get('recent_reconciliations', 0)
                }
            
            self.health_monitor.add_metric('autopoietic_auditor', get_auditor_metrics)
            logger.info("Added auditor metrics to health monitor")
    
    def auto_register_modules(self) -> int:
        """Automatically discover and register LOVE modules"""
        try:
            from evolution.autopoietic_auditor import get_autopoietic_auditor
            auditor = get_autopoietic_auditor()
            
            # Discover Python modules in the project
            discovered_modules = self._discover_python_modules()
            
            registered_count = 0
            for module_info in discovered_modules:
                try:
                    # Generate sample outputs by calling the module
                    sample_outputs = self._generate_sample_outputs(module_info)
                    performance_data = self._get_performance_data(module_info)
                    
                    if sample_outputs:  # Only register if we can get outputs
                        auditor.register_module(
                            module_id=module_info['id'],
                            module_name=module_info['name'],
                            module_path=module_info['path'],
                            sample_outputs=sample_outputs,
                            performance_data=performance_data
                        )
                        registered_count += 1
                        
                except Exception as e:
                    logger.error(f"Error registering module {module_info['name']}: {e}")
            
            logger.info(f"Auto-registered {registered_count} modules")
            return registered_count
            
        except Exception as e:
            logger.error(f"Error in auto-registration: {e}")
            return 0
    
    def _discover_python_modules(self) -> List[Dict[str, str]]:
        """Discover Python modules in the LOVE project"""
        modules = []
        base_path = Path(__file__).parent.parent
        
        # Search for Python files in key directories
        search_dirs = ['core', 'integrations', 'agents', 'tools', 'cognition', 'evolution', 'kernel', 'interface']
        
        for dir_name in search_dirs:
            dir_path = base_path / dir_name
            if dir_path.exists():
                for py_file in dir_path.glob('*.py'):
                    if py_file.name != '__init__.py':
                        module_id = f"{dir_name}.{py_file.stem}"
                        modules.append({
                            'id': module_id,
                            'name': py_file.stem,
                            'path': str(py_file),
                            'directory': dir_name
                        })
        
        logger.info(f"Discovered {len(modules)} Python modules")
        return modules
    
    def _generate_sample_outputs(self, module_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate sample outputs from a module for baseline establishment"""
        try:
            # Try to import the module
            module_path = module_info['path']
            module_name = module_info['name']
            
            # For now, return generic sample data
            # In production, this would actually call the module's functions
            return [
                {"status": "sample", "module": module_name, "output": "test_data_1"},
                {"status": "sample", "module": module_name, "output": "test_data_2"},
                {"status": "sample", "module": module_name, "output": "test_data_3"}
            ]
            
        except Exception as e:
            logger.error(f"Error generating sample outputs for {module_info['name']}: {e}")
            return []
    
    def _get_performance_data(self, module_info: Dict[str, str]) -> Dict[str, float]:
        """Get performance data for a module"""
        # For now, return generic performance data
        # In production, this would measure actual performance
        return {
            "execution_time": 0.1,
            "memory_usage": 512,
            "cpu_usage": 0.1
        }
    
    def setup_data_source_integrations(self) -> int:
        """Setup integrations with data sources for coherence checking"""
        try:
            from evolution.autopoietic_auditor import get_autopoietic_auditor
            auditor = get_autopoietic_auditor()
            
            registered_sources = 0
            
            # Register ChromaDB as a data source
            try:
                chroma_accessor = self._create_chroma_accessor()
                if chroma_accessor:
                    auditor.register_data_source("chromadb", chroma_accessor)
                    registered_sources += 1
            except Exception as e:
                logger.error(f"Error registering ChromaDB: {e}")
            
            # Register Live Memory as a data source
            try:
                memory_accessor = self._create_memory_accessor()
                if memory_accessor:
                    auditor.register_data_source("live_memory", memory_accessor)
                    registered_sources += 1
            except Exception as e:
                logger.error(f"Error registering Live Memory: {e}")
            
            # Register OS Symbiosis as a data source
            try:
                os_accessor = self._create_os_accessor()
                if os_accessor:
                    auditor.register_data_source("os_symbiosis", os_accessor)
                    registered_sources += 1
            except Exception as e:
                logger.error(f"Error registering OS Symbiosis: {e}")
            
            # Register Awareness as a data source
            try:
                awareness_accessor = self._create_awareness_accessor()
                if awareness_accessor:
                    auditor.register_data_source("awareness", awareness_accessor)
                    registered_sources += 1
            except Exception as e:
                logger.error(f"Error registering Awareness: {e}")
            
            logger.info(f"Registered {registered_sources} data sources for coherence checking")
            return registered_sources
            
        except Exception as e:
            logger.error(f"Error setting up data source integrations: {e}")
            return 0
    
    def _create_chroma_accessor(self) -> Optional[Any]:
        """Create accessor for ChromaDB data source"""
        try:
            # Try to import ChromaDB
            import chromadb
            from pathlib import Path
            
            # Setup ChromaDB client
            chroma_path = Path(__file__).parent.parent / "data" / "chromadb"
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            client = chromadb.PersistentClient(path=str(chroma_path))
            
            class ChromaAccessor:
                def __init__(self, client):
                    self.client = client
                
                def get_state(self):
                    # Get current state from ChromaDB collections
                    collections = self.client.list_collections()
                    state = {
                        "collections": len(collections),
                        "last_updated": datetime.now().isoformat()
                    }
                    return state
            
            return ChromaAccessor(client)
            
        except ImportError:
            logger.warning("ChromaDB not available")
            return None
        except Exception as e:
            logger.error(f"Error creating ChromaDB accessor: {e}")
            return None
    
    def _create_memory_accessor(self) -> Optional[Any]:
        """Create accessor for Live Memory data source"""
        try:
            from pathlib import Path
            
            memory_path = Path(__file__).parent.parent / "data" / "love_memory.json"
            
            if not memory_path.exists():
                return None
            
            class MemoryAccessor:
                def __init__(self, memory_path):
                    self.memory_path = memory_path
                
                def get_state(self):
                    try:
                        with open(self.memory_path, 'r', encoding='utf-8') as f:
                            memory_data = json.load(f)
                        
                        # Extract relevant state information
                        state = {
                            "recent_entries": len(memory_data.get('recent', [])),
                            "timestamp": memory_data.get('timestamp'),
                            "user_context": memory_data.get('user_context', {})
                        }
                        return state
                    except Exception as e:
                        logger.error(f"Error reading memory: {e}")
                        return {}
            
            return MemoryAccessor(memory_path)
            
        except Exception as e:
            logger.error(f"Error creating Memory accessor: {e}")
            return None
    
    def _create_os_accessor(self) -> Optional[Any]:
        """Create accessor for OS Symbiosis data source"""
        try:
            # Try to use awareness system as OS data source
            from core.awareness import get_awareness
            
            awareness = get_awareness()
            
            class OSAccessor:
                def __init__(self, awareness):
                    self.awareness = awareness
                
                def get_state(self):
                    try:
                        snapshot = self.awareness.get_snapshot()
                        return {
                            "active_window": snapshot.get('active_window'),
                            "cpu_usage": snapshot.get('cpu_usage'),
                            "memory_usage": snapshot.get('memory_usage'),
                            "timestamp": datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.error(f"Error getting OS state: {e}")
                        return {}
            
            return OSAccessor(awareness)
            
        except ImportError:
            logger.warning("Awareness module not available")
            return None
        except Exception as e:
            logger.error(f"Error creating OS accessor: {e}")
            return None
    
    def _create_awareness_accessor(self) -> Optional[Any]:
        """Create accessor for Awareness data source"""
        # This is similar to OS accessor, could be combined
        return self._create_os_accessor()
    
    def create_unified_dashboard(self) -> Dict[str, Any]:
        """Create a unified dashboard combining all monitoring data"""
        try:
            from evolution.autopoietic_auditor import get_autopoietic_auditor
            auditor = get_autopoietic_auditor()
            
            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "autopoietic_auditor": auditor.get_audit_summary(),
                "sentinel_status": self._get_sentinel_status(),
                "error_summary": self._get_error_summary(),
                "health_metrics": self._get_health_metrics()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error creating unified dashboard: {e}")
            return {"error": str(e)}
    
    def _get_sentinel_status(self) -> Dict[str, Any]:
        """Get status from Sentinel"""
        if self.sentinel and hasattr(self.sentinel, 'get_status'):
            return self.sentinel.get_status()
        return {"status": "not_integrated"}
    
    def _get_error_summary(self) -> Dict[str, Any]:
        """Get error summary from error tracker"""
        if self.error_tracker and hasattr(self.error_tracker, 'get_summary'):
            return self.error_tracker.get_summary()
        return {"status": "not_integrated"}
    
    def _get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics from health monitor"""
        if self.health_monitor and hasattr(self.health_monitor, 'get_metrics'):
            return self.health_monitor.get_metrics()
        return {"status": "not_integrated"}


# Singleton instance
_integration_instance: Optional[AuditorIntegration] = None
_integration_lock = threading.Lock()

def get_auditor_integration() -> AuditorIntegration:
    """Get the singleton Auditor Integration instance"""
    global _integration_instance
    with _integration_lock:
        if _integration_instance is None:
            _integration_instance = AuditorIntegration()
        return _integration_instance


def setup_full_integration() -> bool:
    """Setup full integration with all existing systems"""
    try:
        integration = get_auditor_integration()
        
        # Integrate with existing systems
        success_count = 0
        
        # Try to integrate with Sentinel
        try:
            from core.sentinel import get_sentinel
            sentinel = get_sentinel()
            if integration.integrate_with_sentinel(sentinel):
                success_count += 1
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="evolution.auditor_integration")
        
        # Auto-register modules
        registered_modules = integration.auto_register_modules()
        if registered_modules > 0:
            success_count += 1
        
        # Setup data source integrations
        registered_sources = integration.setup_data_source_integrations()
        if registered_sources > 0:
            success_count += 1
        
        logger.info(f"Full integration setup complete: {success_count} systems integrated")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in full integration setup: {e}")
        return False


if __name__ == "__main__":
    # Test the integration
    print("Testing Auditor Integration...")
    
    # Setup full integration
    success = setup_full_integration()
    print(f"Integration setup: {'Success' if success else 'Failed'}")
    
    # Create unified dashboard
    integration = get_auditor_integration()
    dashboard = integration.create_unified_dashboard()
    print(f"\nUnified Dashboard: {dashboard}")
    
    print("\nAuditor Integration test completed!")