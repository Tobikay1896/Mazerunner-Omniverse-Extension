import omni.usd
from pxr import Sdf, UsdPhysics, UsdGeom, Gf, Usd


SUCTION_TARGET_PATH = "/World/Production_Line/Deckelmagazin/Deckel"
SUCTION_GRIPPER_MESH_PATH = "/World/Production_Line/Schwenkarm_Deckel/Schwenkarm_Deckel_move_translatory/Schwenkarm_Deckel_move_rotatory/tn__Saubnapf1_zH/tn__Volumenkrper2_gm2/Mesh"
SUCTION_JOINT_PATH = "/World/Production_Line/SaugnapfDeckelJoint"


class SuctionGripper:
    def __init__(self, ext=None):
        self._ext = ext
        self._active = False

    def _log(self, msg, level="info"):
        if self._ext and hasattr(self._ext, "_log"):
            self._ext._log(msg, level)
        else:
            print(f"[Suction] {msg}")

    def _stage(self):
        return omni.usd.get_context().get_stage()

    def _find_rigidbody_ancestor(self, prim):
        current = prim
        while current and current.IsValid():
            if current.HasAPI(UsdPhysics.RigidBodyAPI):
                return current
            current = current.GetParent()
        return None

    def joint_exists(self):
        stage = self._stage()
        if not stage:
            return False
        return stage.GetPrimAtPath(SUCTION_JOINT_PATH).IsValid()

    def remove_joint(self):
        stage = self._stage()
        if not stage:
            return
        if stage.GetPrimAtPath(SUCTION_JOINT_PATH).IsValid():
            stage.RemovePrim(SUCTION_JOINT_PATH)
            self._log(f"Joint entfernt: {SUCTION_JOINT_PATH}", "info")

    def reset(self):
        self.remove_joint()
        self._active = False
        self._log("Reset", "info")

    def detach(self):
        self.remove_joint()
        self._active = False
        self._log("Sauggreifer AUS", "ok")

    def attach(self):
        stage = self._stage()
        if not stage:
            self._log("Keine Stage vorhanden", "error")
            return False

        time = Usd.TimeCode.Default()

        gripper_prim = stage.GetPrimAtPath(SUCTION_GRIPPER_MESH_PATH)
        target_prim = stage.GetPrimAtPath(SUCTION_TARGET_PATH)

        if not gripper_prim.IsValid():
            self._log(f"Greifer-Mesh nicht gefunden: {SUCTION_GRIPPER_MESH_PATH}", "error")
            return False

        if not target_prim.IsValid():
            self._log(f"Deckel nicht gefunden: {SUCTION_TARGET_PATH}", "error")
            return False

        body0_prim = self._find_rigidbody_ancestor(gripper_prim)
        if body0_prim is None:
            self._log("Kein RigidBody-Vorfahre für Greifer gefunden", "error")
            return False

        body0_path = str(body0_prim.GetPath())
        self._log(f"Body0 gefunden: {body0_path}", "info")

        if not target_prim.HasAPI(UsdPhysics.RigidBodyAPI):
            rb = UsdPhysics.RigidBodyAPI.Apply(target_prim)
            rb.CreateRigidBodyEnabledAttr(True)
            self._log("RigidBodyAPI auf Deckel angewendet", "info")

        gripper_world = UsdGeom.Xformable(gripper_prim).ComputeLocalToWorldTransform(time)
        gripper_world_pos = gripper_world.ExtractTranslation()

        parent_prim = target_prim.GetParent()
        if not parent_prim.IsValid():
            self._log("Deckel-Parent ungültig", "error")
            return False

        parent_world = UsdGeom.Xformable(parent_prim).ComputeLocalToWorldTransform(time)
        parent_inv = parent_world.GetInverse()

        local_pos = parent_inv.Transform(gripper_world_pos)

        self._log(f"Gripper World: {gripper_world_pos}", "info")
        self._log(f"Deckel Local Ziel: {local_pos}", "info")

        xform = UsdGeom.Xformable(target_prim)
        translate_op = None

        for op in xform.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                translate_op = op
                break

        if translate_op is None:
            translate_op = xform.AddTranslateOp()

        translate_op.Set(Gf.Vec3d(
            float(local_pos[0]),
            float(local_pos[1]),
            float(local_pos[2])
        ))

        target_world_after = UsdGeom.Xformable(target_prim).ComputeLocalToWorldTransform(time)
        diff = target_world_after.ExtractTranslation() - gripper_world_pos

        self._log(f"Target World nach Teleport: {target_world_after.ExtractTranslation()}", "info")
        self._log(f"Diff zu Gripper: {diff}", "info")

        body0_world = UsdGeom.Xformable(body0_prim).ComputeLocalToWorldTransform(time)
        body0_inv = body0_world.GetInverse()
        contact_in_body0 = body0_inv.Transform(gripper_world_pos)

        self.remove_joint()

        joint = UsdPhysics.FixedJoint.Define(stage, SUCTION_JOINT_PATH)
        joint.GetBody0Rel().SetTargets([Sdf.Path(body0_path)])
        joint.GetBody1Rel().SetTargets([Sdf.Path(SUCTION_TARGET_PATH)])

        joint.GetLocalPos0Attr().Set(Gf.Vec3f(
            float(contact_in_body0[0]),
            float(contact_in_body0[1]),
            float(contact_in_body0[2]),
        ))
        joint.GetLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

        joint.GetLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        joint.GetLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

        self._active = True
        self._log("Sauggreifer EIN ✅", "ok")
        return True

    def toggle(self):
        if self.joint_exists():
            self.detach()
            return False
        else:
            ok = self.attach()
            return ok

    @property
    def is_active(self):
        return self.joint_exists()