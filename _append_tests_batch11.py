with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Document Organizer Tests -----------------------------------------------

class TestDocumentOrganizer:
    """Test Document Organizer."""
    
    def test_singleton(self):
        from core.document_organizer import get_document_organizer
        d1 = get_document_organizer()
        d2 = get_document_organizer()
        assert d1 is d2
    
    def test_record_document(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        doc = do.record_document(
            "Contract 2024",
            "contract",
            ["legal", "2024"],
            "high",
            "/docs/contracts/2024.pdf",
            1024,
            "2025-12-31",
        )
        assert doc is not None
        assert doc.name == "Contract 2024"
        assert doc.importance == "high"
        assert "legal" in doc.tags
    
    def test_access_document(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        doc = do.record_document("Test Doc", "note")
        accessed = do.access_document(doc.doc_id)
        assert accessed is not None
        assert accessed.access_count >= 1
    
    def test_get_document_stats(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        stats = do.get_document_stats()
        assert isinstance(stats, dict)
    
    def test_get_retrieval_suggestions(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        do.record_document("Tax Return 2024", "report", ["finance", "tax"], "high")
        suggestions = do.get_retrieval_suggestions("tax finance")
        assert isinstance(suggestions, list)
    
    def test_get_organization_score(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        score = do.get_organization_score()
        assert 0 <= score <= 100


# -- Password Health Checker Tests ------------------------------------------

class TestPasswordHealthChecker:
    """Test Password Health Checker."""
    
    def test_singleton(self):
        from core.password_health_checker import get_password_health_checker
        p1 = get_password_health_checker()
        p2 = get_password_health_checker()
        assert p1 is p2
    
    def test_record_account(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        account = phc.record_account(
            "Bank", "user123", 30, 0.9, True, "critical", "financial"
        )
        assert account is not None
        assert account.service == "Bank"
        assert account.has_2fa is True
    
    def test_get_password_health(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        health = phc.get_password_health()
        assert isinstance(health, dict)
        assert "overall_score" in health
    
    def test_get_risk_assessment(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        phc.record_account("OldSite", "user", 200, 0.2, False, "high", "social")
        risks = phc.get_risk_assessment()
        assert isinstance(risks, list)
        if risks:
            assert "risk_score" in risks[0]
    
    def test_get_security_recommendations(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        recs = phc.get_security_recommendations()
        assert isinstance(recs, list)


# -- Subscription Manager Tests ---------------------------------------------

class TestSubscriptionManager:
    """Test Subscription Manager."""
    
    def test_singleton(self):
        from core.subscription_manager import get_subscription_manager
        s1 = get_subscription_manager()
        s2 = get_subscription_manager()
        assert s1 is s2
    
    def test_record_subscription(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("Netflix", 15.99, "monthly", "streaming", "Netflix Inc", "2025-06-15")
        assert sub is not None
        assert sub.name == "Netflix"
        assert sub.cost == 15.99
    
    def test_record_usage(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("Spotify", 9.99, "monthly", "music")
        usage = sm.record_usage(sub.sub_id, 120, "playlist")
        assert usage is not None
        assert usage.sub_id == sub.sub_id
    
    def test_get_subscription_stats(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        stats = sm.get_subscription_stats()
        assert isinstance(stats, dict)
    
    def test_get_optimization_suggestions(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        suggestions = sm.get_optimization_suggestions()
        assert isinstance(suggestions, list)
    
    def test_cancel_subscription(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("TempSub", 5.0, "monthly", "test")
        sm.cancel_subscription(sub.sub_id)
        assert not sm._subscriptions[sub.sub_id].is_active


# -- Digital Declutterer Tests ----------------------------------------------

class TestDigitalDeclutterer:
    """Test Digital Declutterer."""
    
    def test_singleton(self):
        from core.digital_declutterer import get_digital_declutterer
        d1 = get_digital_declutterer()
        d2 = get_digital_declutterer()
        assert d1 is d2
    
    def test_record_storage_scan(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        record = dd.record_storage_scan("downloads", 25.5, 150, [], [])
        assert record is not None
        assert record.category == "downloads"
        assert record.size_gb == 25.5
    
    def test_record_app_usage(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        usage = dd.record_app_usage("VS Code", 240, "work", True)
        assert usage is not None
        assert usage.app_name == "VS Code"
        assert usage.was_productive is True
    
    def test_get_clutter_score(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        score = dd.get_clutter_score()
        assert 0 <= score <= 100
    
    def test_get_declutter_plan(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        plan = dd.get_declutter_plan()
        assert isinstance(plan, list)
    
    def test_get_digital_wellness_score(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        score = dd.get_digital_wellness_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 11 tests successfully')
